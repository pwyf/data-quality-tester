from collections import OrderedDict
from datetime import datetime
from enum import Enum
import json
from os import makedirs
from os.path import join
from urllib.parse import urlparse
import uuid

from foxpath import Foxpath
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

    def parse(self):
        try:
            doc = etree.parse(self.path_to_file())
        except OSError:
            raise FileGoneException('Sorry – The file no longer exists.')
        except etree.XMLSyntaxError:
            raise InvalidXMLException('The file does not appear to be a valid XML file.')
        return doc

    def get_activities(self):
        return self.parse().xpath('//iati-activity')

    def get_activity(self, iati_identifier):
        doc = self.parse()
        activities = doc.xpath('//iati-activity/iati-identifier[text()="{}"]/..'.format(iati_identifier))
        if len(activities) != 1:
            raise ActivityNotFoundException('The requested activity couldn\'t be found in that file.')
        return Activity(activities[0])

    def is_valid(self, url):
        qualifying = ('scheme', 'netloc',)
        token = urlparse(url)
        return all([getattr(token, qualifying_attr)
            for qualifying_attr in qualifying])

    def upload_dir(self):
        return join(app.config['MEDIA_FOLDER'], self.id)

    def path_to_file(self):
        return join(app.config['MEDIA_FOLDER'], self.original_file)

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

    def get_results(self, tests, filter_=None, iati_identifier=None):
        return Results(self, tests, filter_, iati_identifier)

class Activity():
    def __init__(self, el):
        self.el = el

    def __str__(self):
        return etree.tostring(self.el, pretty_print=True).strip().decode('utf-8')

class Results():
    def __init__(self, supplied_data, tests, filter_=None, iati_identifier=None):
        self.supplied_data = supplied_data
        self.tests = tests
        self.filter_ = filter_
        self.iati_identifier = iati_identifier
        self.all = self.generate(tests, filter_, iati_identifier)
        summary = Foxpath.summarize_results(self.all)
        self.by_test = OrderedDict(zip([x['name'] for x in tests], summary))

    def generate(self, tests, filter_, iati_identifier):
        foxpath = Foxpath()
        foxtests = foxpath.load_tests(tests, app.config['CODELISTS'])
        if iati_identifier:
            activity = self.get_activity(iati_identifier)
            results = foxpath.test_activities([activity], foxtests)
        try:
            results = self.load_cache(filter_ is not None)
        except FileNotFoundError:
            activities = self.supplied_data.get_activities()
            if filter_:
                activities = self.filter_activities(activities, filter_)
            results = foxpath.test_activities(activities, foxtests)
            self.save_cache(results, filter_ is not None)
        return results

    def filter_activities(self, activities, filter_):
        foxpath = Foxpath()
        foxtests = foxpath.load_tests([filter_], app.config['CODELISTS'])
        activities_results = foxpath.test_activities(activities, foxtests)

        filtered_activities = []
        for idx, activity in enumerate(activities):
            if activities_results[idx]['results'][0] == 1:
                filtered_activities.append(activity)

        return filtered_activities

    def path_to_file(self, filtering):
        return join(self.supplied_data.upload_dir(), 'results-pwyf-{}.json').format('filtered' if filtering else 'all')

    def save_cache(self, results, filtering):
        filepath = self.path_to_file(filtering)
        with open(filepath, 'w') as f:
            json.dump(results, f)

    def load_cache(self, filtering):
        filepath = self.path_to_file(filtering)
        with open(filepath) as f:
            j = json.load(f)
        return j

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

    def get_fails(self):
        for activity in self.all:
            pass

    @property
    def percentages(self):
        print(self.by_test)
        percs = [(k, v[1] / (v[1] + v[0])) for k, v in self.by_test.items() if v[1] + v[0] > 0]
        return OrderedDict(sorted(percs, key=lambda x: x[1], reverse=True))
