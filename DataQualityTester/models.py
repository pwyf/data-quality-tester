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

    def test(self, tests):
        foxpath = Foxpath()
        foxtests = foxpath.load_tests(tests, app.config['CODELISTS'])
        results = foxpath.test_activity(
            self.el,
            foxtests,
            explain=True
        )['results']
        grouped = {
            0: [],
            1: [],
            -1: [],
        }
        for test_name, out in results.items():
            grouped[out[0]].append((test_name, out[1]))
        return grouped


class TestSet():
    def __init__(self, test_set_id):
        if test_set_id in app.config['TEST_SETS']:
            self.id = test_set_id
        else:
            self.id = app.config['DEFAULT_TEST_SET']
        test_set = app.config['TEST_SETS'][self.id]
        self.name = test_set['name']
        self.description = test_set['description']
        self.components = test_set['components']
        self.filepath = test_set['filepath']

    @property
    def all_test_sets(self):
        return [(x, y['name']) for x, y in app.config['TEST_SETS'].items()]

    @property
    def all_tests(self):
        return [t for c in self.components.values()
                for i in c.indicators
                for t in i['tests']]

    def get_test(self, test_name):
        return {t['name']: t for t in self.all_tests}[test_name]


class Component():
    def __str__(self):
        return self.name

    def __init__(self, name, indicators):
        self.name = name
        self.indicators = indicators

    @property
    def tests(self):
        return [t['name'] for i in self.indicators for t in i['tests']]


class Results():
    def __init__(self, supplied_data, test_set,
                 current_tests=None, filter_=None):
        self.supplied_data = supplied_data
        self.test_set = test_set
        self.filter = filter_
        self.all, self.meta = self._test_and_cache(test_set.all_tests)
        if self.all == []:
            return
        if current_tests:
            for x in self.all:
                x['results'] = dict(filter(
                    lambda y: y[0] in current_tests, x['results'].items()))
        # summary by test
        self.summary_by_test = Foxpath.summarize_results(self.all)

    def for_test(self, test_name, score=None):
        results = [{
            'title': x['title'],
            'iati-identifier': x['iati-identifier'],
            'hierarchy': x['hierarchy'],
            'score': x['results'][test_name][0],
            'explanation': helpers.pprint(x['results'][test_name][1]),
        } for x in self.all]
        if score is not None:
            results = list(filter(lambda x: x['score'] == score, results))
        return results

    def _test_and_cache(self, tests):
        meta = {}
        foxpath = Foxpath()
        foxtests = foxpath.load_tests(tests, app.config['CODELISTS'])
        try:
            results = self.load_cache(self.path_to_file())
        except FileNotFoundError:
            xml = self.supplied_data.parse()
            reporting_org_strs = xml.xpath(
                '//reporting-org/text() | //reporting-org/narrative/text()')
            for reporting_org_str in reporting_org_strs:
                reporting_org = reporting_org_str.strip()
                if reporting_org != '':
                    break
            if reporting_org != '':
                meta['reporting_org'] = reporting_org
            else:
                meta['reporting_org'] = None
            activities = xml.xpath('//iati-activity')
            meta['total_activities'] = len(activities)
            if self.filter:
                activities = Results.filter_activities(activities, self.filter)
                meta['total_filtered_activities'] = len(activities)
                self.save_cache(
                    meta,
                    join(self.supplied_data.upload_dir(), 'meta.json'))
            results = foxpath.test_activities(
                activities,
                foxtests,
                explain=True)
            self.save_cache(results, self.path_to_file())

        if 'total_filtered_activities' not in meta:
            try:
                meta = self.load_cache(
                    join(self.supplied_data.upload_dir(), 'meta.json'))
            except FileNotFoundError:
                pass

        return results, meta

    @staticmethod
    def filter_activities(activities, filter_):
        foxpath = Foxpath()
        foxtests = foxpath.load_tests([filter_], app.config['CODELISTS'])
        activities_results = foxpath.test_activities(activities, foxtests)

        filtered_activities = []
        for idx, activity in enumerate(activities):
            if activities_results[idx]['results'][filter_['name']] == 1:
                filtered_activities.append(activity)

        return filtered_activities

    def path_to_file(self):
        filtering = 'filtered' if self.filter is not None else 'all'
        filename = 'results-{test_set_id}-{filtering}.json'.format(
            test_set_id=self.test_set.id,
            filtering=filtering)
        return join(self.supplied_data.upload_dir(), filename)

    def save_cache(self, results, filepath):
        with open(filepath, 'w') as f:
            json.dump(results, f)

    def load_cache(self, filepath):
        with open(filepath) as f:
            j = json.load(f)
        return j

    # percentages by test, sorted
    @property
    def percentages(self):
        percs = [
            (k, v[1] / (v[1] + v[0]))
            for k, v in self.summary_by_test.items()
            if v[1] + v[0] > 0]
        return OrderedDict(sorted(percs, key=lambda x: x[1], reverse=True))
