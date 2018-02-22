from datetime import datetime
from enum import Enum
from os import listdir, makedirs
from os.path import join
import re
from urllib.parse import urlparse
import uuid

from lxml import etree
from werkzeug.utils import secure_filename

from DataQualityTester import app, db
from DataQualityTester.tasks import download_task
from DataQualityTester.lib import helpers
from DataQualityTester.lib.exceptions import (
    BadUrlException, FileGoneException,
    InvalidXMLException, ActivityNotFoundException)


class SuppliedData(db.Model):
    class FormName(Enum):
        upload_form = 'File upload'
        url_form = 'Downloaded from URL'
        text_form = 'Pasted into textarea'

    id = db.Column(db.String(40), primary_key=True)
    source_url = db.Column(db.String(2000))
    original_file = db.Column(db.String(100))

    downloaded = db.Column(db.Boolean(True))
    task_id = db.Column(db.String(100))

    form_name = db.Column(db.Enum(FormName))
    created = db.Column(db.DateTime)

    def allowed_file_extension(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() \
            in app.config['ALLOWED_EXTENSIONS']

    def generate_uuid(self):
        return str(uuid.uuid4())

    def parse(self):
        try:
            doc = etree.parse(self.path_to_file())
        except OSError:
            raise FileGoneException('Sorry – The file no longer exists.')
        except etree.XMLSyntaxError:
            raise InvalidXMLException(
                'The file does not appear to be a valid XML file.')
        return doc

    @property
    def name(self):
        if self.form_name == self.FormName.url_form:
            return 'The <a href="{url}">linked IATI data</a>'.format(
                url=self.source_url)
        if self.form_name == self.FormName.upload_form:
            return 'The uploaded IATI data'
        return 'The pasted IATI data'

    def get_activities(self):
        return self.parse().xpath('//iati-activity')

    def get_activity(self, iati_identifier):
        doc = self.parse()
        activities = doc.xpath(
            '//iati-activity/iati-identifier[text()="{}"]/..'.format(
                iati_identifier))
        if len(activities) != 1:
            raise ActivityNotFoundException(
                'The requested activity couldn\'t be found in that file.')
        return Activity(activities[0])

    def is_valid(self, url):
        qualifying = ('scheme', 'netloc',)
        token = urlparse(url)
        return all([
            getattr(token, qualifying_attr) for qualifying_attr in qualifying
        ])

    def upload_dir(self):
        return join(app.config['MEDIA_FOLDER'], self.id)

    def path_to_file(self):
        return join(app.config['MEDIA_FOLDER'], self.original_file)

    def start_download(self):
        task = download_task.delay(self.id)
        return task.id

    def __init__(self, source_url, file, raw_text, form_name):
        self.id = self.generate_uuid()

        if form_name == 'url_form':
            if not self.is_valid(source_url):
                raise BadUrlException('That source URL appears to be ' +
                                      'invalid. Please try again.')
            self.downloaded = False
            filename = None
            self.task_id = self.start_download()
        elif form_name == 'upload_form':
            filename = file.filename
            if filename != '' and self.allowed_file_extension(filename):
                # save the file
                filename = secure_filename(filename)
                makedirs(self.upload_dir(), exist_ok=True)
                filepath = join(self.upload_dir(), filename)
                file.save(filepath)
        else:
            filename = 'test.xml'
            makedirs(self.upload_dir(), exist_ok=True)
            filepath = join(self.upload_dir(), filename)
            with open(filepath, 'w') as f:
                f.write(raw_text)

        self.source_url = source_url
        if filename:
            self.original_file = join(self.id, filename)
        self.form_name = form_name

        self.created = datetime.utcnow()


class Activity():
    def __init__(self, el):
        self.el = el

    def __str__(self):
        return etree.tostring(
            self.el,
            pretty_print=True
        ).strip().decode('utf-8')


class TestSet():
    def __init__(self, test_set_id):
        if test_set_id in app.config['TEST_SETS']:
            self.id = test_set_id
        else:
            self.id = app.config['DEFAULT_TEST_SET']
        test_set = app.config['TEST_SETS'][self.id]
        self.name = test_set['name']
        self.description = test_set['description']
        self.filepath = test_set['filepath']
        cs = test_set['components']
        self.components = [Component(*c, filepath=self.filepath) for c in cs]

    def get_component(self, component_id):
        return {c.id: c for c in self.components}.get(component_id)


class Component():
    def __repr__(self):
        return '<Component: {}>'.format(self.name)

    def __init__(self, id_, name, filepath):
        self.id = id_
        self.name = name
        self.filepath = join(filepath, id_)

    def get_test(self, test_name):
        test_prefix = r'Scenario(?: Outline)?\:'
        test_expression_re = re.compile(
            r'{prefix} {name}(.*?)(?:{prefix}|$)'.format(
                prefix=test_prefix,
                name=re.escape(test_name),
            ), re.DOTALL)
        for feature in listdir(self.filepath):
            if not feature.endswith('.feature'):
                continue
            filepath = join(self.filepath, feature)
            with open(filepath) as f:
                feature_text = f.read()
            match = test_expression_re.search(feature_text)
            if match:
                test_expression = match.group(1).strip()
                line_num = len(feature_text[:match.start()].split('\n'))
                break
        return Test(test_name, test_expression, filepath, line_num)


class Test():
    def __init__(self, name, expression, filepath, line_num):
        self.id = secure_filename(name)
        self.name = name
        self.expression = expression
        self.filepath = filepath
        self.line_num = line_num

    @property
    def rendered(self):
        return helpers.pprint(self.expression)
