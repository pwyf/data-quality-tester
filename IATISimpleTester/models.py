from datetime import datetime
from enum import Enum
import json
from os import makedirs
from os.path import join
from urllib.parse import urlparse
import uuid

from lxml import etree
import requests
import rfc6266  # (content-disposition header parser)
from werkzeug.utils import secure_filename

from IATISimpleTester import app, db
from IATISimpleTester.lib import helpers
from IATISimpleTester.lib.exceptions import BadUrlException, FileGoneException, InvalidXMLException, ActivityNotFoundException


class SuppliedData(db.Model):
    class FormName(Enum):
        upload_form = 'File upload'
        url_form = 'Downloaded from URL'
        text_form = 'Pasted into textarea'


    id = db.Column(db.String(40), primary_key=True)
    source_url = db.Column(db.String(2000))
    original_file = db.Column(db.String(100))
    form_name = db.Column(db.Enum(FormName))
    created = db.Column(db.DateTime)

    def allowed_file_extension(self, filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def generate_uuid(self):
       return str(uuid.uuid4())

    def is_valid(self, url):
        qualifying = ('scheme', 'netloc',)
        token = urlparse(url)
        return all([getattr(token, qualifying_attr)
            for qualifying_attr in qualifying])

    def upload_dir(self):
        return join(app.config['MEDIA_FOLDER'], self.id)

    def path_to_file(self):
        return join(app.config['MEDIA_FOLDER'], self.original_file)

    def parse(self, iati_identifier=None):
        try:
            doc = etree.parse(self.path_to_file())
        except OSError:
            raise FileGoneException('Sorry – The file no longer exists.')
        except etree.XMLSyntaxError:
            raise InvalidXMLException('The file does not appear to be a valid XML file.')
        if iati_identifier:
            activity = doc.xpath('//iati-activity/iati-identifier[text()="{}"]/..'.format(iati_identifier))
            if len(activity) != 1:
                raise ActivityNotFoundException('The requested activity couldn\'t be found in that file.')
            return activity[0]
        return doc.xpath('//iati-activity')

    def download(self, url):
        if not self.is_valid(url):
            raise BadUrlException('That source URL appears to be invalid. Please try again.')
        r = requests.get(url, headers={'User-Agent': 'Publish What You Fund Simple Tester'}, stream=True)
        r.raise_for_status()
        content_type = r.headers.get('content-type', '').split(';')[0].lower()
        file_extension = None
        if content_type in ('text/xml', 'application/xml',):
            file_extension = 'xml'

        if not file_extension:
            possible_extension = rfc6266.parse_requests_response(r).filename_unsafe.split('.')[-1]
            if possible_extension == 'xml':
                file_extension = possible_extension

        filename = r.url.split('/')[-1].split('?')[0][:100]
        if filename == '':
            filename = 'file'
        if file_extension:
            if not filename.endswith(file_extension):
                filename = filename + '.' + file_extension
        filename = secure_filename(filename)
        makedirs(self.upload_dir(), exist_ok=True)
        filepath = join(self.upload_dir(), filename)
        with open(filepath, 'wb') as f:
            for block in r.iter_content(1024):
                f.write(block)
        return filename

    def __init__(self, source_url, file, raw_text, form_name):
        self.id = self.generate_uuid()

        if source_url:
            filename = self.download(source_url)
        elif file:
            if file.filename != '' and self.allowed_file_extension(file.filename):
                # save the file
                filename = file.filename
                filename = secure_filename(filename)
                makedirs(self.upload_dir(), exist_ok=True)
                filepath = join(self.upload_dir(), filename)
                file.save(filepath)
        elif raw_text:
            filename = 'test.xml'
            makedirs(self.upload_dir(), exist_ok=True)
            filepath = join(self.upload_dir(), filename)
            with open(filepath, 'w') as f:
                f.write(raw_text)

        self.source_url = source_url
        self.original_file = join(self.id, filename)
        self.form_name = form_name

        self.created = datetime.utcnow()

    def get_results(self, test_set_id, filtering):
        return Results(self, test_set_id, filtering)


class Results():
    def __init__(self, supplied_data, test_set_id, filtering):
        # these are set by compute_results()

        self.supplied_data = supplied_data
        self.test_set_id = test_set_id
        self.tests, self.filtering, self.filter = self.load_tests_and_filter(filtering)
        data = self.load()
        if not data:
            data = self.compute_results()
        self.total_activities = data['total_activities']
        self.total_filtered_activities = data['total_filtered_activities']
        self.by_test = data['by_test']
        self.save()

    def get_path(self):
        filename = 'results-{test_set_id}-{filter_name}.json'.format(
            test_set_id=self.test_set_id,
            filter_name='filtered' if self.filtering else 'all',
        )
        return join(self.supplied_data.upload_dir(), filename)

    def load(self):
        path_to_results = self.get_path()
        try:
            with open(path_to_results) as f:
                j = json.load(f)
        except FileNotFoundError:
            return False
        return j

    def load_tests_and_filter(self, filtering):
        # load the tests
        test_set = app.config['TEST_SETS'][self.test_set_id]
        test_data = helpers.load_from_yaml(test_set['tests_file'])
        tests = [t for i in test_data['indicators'] for t in i['tests']]
        # set the filter
        if filtering and 'filter' in test_data:
            filter_ = test_data['filter']
        else:
            filter_ = None
            filtering = False
        return tests, filtering, filter_

    # page = int(request.args.get('page', 1))
    # offset = (page - 1) * app.config['PER_PAGE']
    # pagination = Pagination(page, app.config['PER_PAGE'], len(activities))
    # activities_results = activities_results[offset:offset + app.config['PER_PAGE']]

    # components = OrderedDict([(c['name'], c['indicators']) for c in test_data['components']])
    # indicators = OrderedDict([(i['name'], [test['name'] for test in i['tests']]) for i in test_data['indicators']])
    # perc_by_indicator = helpers.group_by(indicators, perc_by_test)

    # component = request.args.get('component')
    # if component:
    #     params['component'] = component
    #     context['results'] = OrderedDict([(k, v) for k, v in perc_by_indicator.items() if k in components[component]])
    # else:
    #     perc_by_component = helpers.group_by(components, perc_by_indicator)
    #     context['results'] = perc_by_component

    def compute_results(self):
        all_activities = self.supplied_data.parse()
        total_activities = len(all_activities)

        total_filtered_activities = None
        if self.filter:
            filtered_activities = helpers.filter_activities(all_activities, self.filter)
            total_filtered_activities = len(filtered_activities)

        activities = filtered_activities if self.filtering else all_activities

        activities_results, by_test = helpers.test_activities(activities, self.tests)
        return {
            'total_activities': total_activities,
            'total_filtered_activities': total_filtered_activities,
            'by_test': by_test,
        }

    def save(self):
        with open(self.get_path(), 'w') as f:
            data = {
                'total_activities': self.total_activities,
                'total_filtered_activities': self.total_filtered_activities,
                'by_test': self.by_test,
            }
            json.dump(data, f)
