import csv
import json
from glob import glob
from os.path import exists, join
from os import makedirs

from bdd_tester import BDDTester
from lxml import etree
import requests
from werkzeug.utils import secure_filename

from DataQualityTester import app, celery, db


def _colorify(number):
    if number is None:
        return '#222'
    # Methodology colours:
    colours = (
        ((180, 96, 122), 0),
        ((232, 152, 77), 25),
        ((248, 204, 78), 50),
        ((159, 175, 52), 75),
        ((108, 137, 178), 100),
    )
    prev_colour, prev_perc = colours[0]
    for colour, perc in colours[1:]:
        if number <= perc:
            dist = (number - prev_perc) / (perc - prev_perc)
            rgb = (int(dist * (colour[d] - prev_colour[d]) + prev_colour[d])
                   for d in range(3))
            return 'rgb({}, {}, {})'.format(*rgb)
        prev_colour = colour
        prev_perc = perc


def _compute_score(results):
    scores = []
    for summary in results.values():
        total = summary['passed'] + summary['failed']
        if total != 0:
            score = summary['passed'] / total
            scores.append(score)
    if len(scores) > 0:
        return 100. * sum(scores) / len(scores)
    else:
        return None


def _load_codelists():
    all_codes = {}
    codelist_list = app.config.get('CODELIST_LIST')
    for codelist in codelist_list:
        codes = []
        for ver in ['1', '2']:
            with open(join('codelists', ver, codelist + '.json')) as f:
                codelist_data = json.load(f)['data']
                codes += [x['code'] for x in codelist_data]
        all_codes[codelist] = codes
    return all_codes


@celery.task(bind=True)
def test_file_task(self, path_to_file, component_path, component_id,
                   output_path):
    results_path = '{}.json'.format(join(output_path, component_id))
    if exists(results_path):
        with open(results_path) as f:
            results = json.load(f)
        score = _compute_score(results)
        if score is not None:
            colour = _colorify(score)
        else:
            colour = '#222'
    else:
        # TODO: handle parse error
        xml = etree.parse(path_to_file)

        step_def_path = join(component_path, '..', 'step_definitions.py')
        filter_path = join(component_path, '..', 'current_data.feature')
        features_paths = glob(join(component_path, '*.feature'))

        tester = BDDTester(step_def_path)
        features = [tester.load_feature(f) for f in features_paths]
        total_tests = sum([len(f.tests) for f in features]) + 1

        activities = xml.findall('iati-activity')
        filter_ = tester.load_feature(filter_path).tests[0]
        filtered_activities = [a for a in activities if filter_(a) is True]

        elements = filtered_activities + xml.findall('iati-organisation')

        codelists = _load_codelists()

        results = {}
        lookup = {True: 'passed', False: 'failed', None: 'not-relevant'}
        counter = 1
        for feature in features:
            for test in feature.tests:
                self.update_state(
                    state='RUNNING',
                    meta={
                        'name': component_id,
                        'progress': 100. * counter / total_tests,
                    }
                )
                counter += 1
                result = {x: 0 for x in lookup.values()}
                current_test = 'Given the activity is current'
                test.steps = [s for s in test.steps if str(s) != current_test]
                fn = '{}.csv'.format(secure_filename(str(test)))
                with open(join(output_path, fn), 'w') as f:
                    csv_file = csv.writer(f)
                    csv_file.writerow(('IATI Identifier', 'Message'))
                    for el in elements:
                        out = test(el,
                                   codelists=codelists,
                                   bdd_verbose=True)

                        result[lookup.get(out[0])] += 1
                        if out[0] is False:
                            iati_identifier = None
                            xpath_result = el.xpath(
                                'iati-identifier[1]/text()'
                            )
                            if len(xpath_result) > 0:
                                iati_identifier = str(xpath_result[0])
                            csv_file.writerow(
                                [iati_identifier, str(out[1].args[1])]
                            )

                    results[str(test)] = result
                    score = _compute_score(results)
                    if score is not None:
                        colour = _colorify(score)
                    else:
                        colour = '#222'
        # cache the result
        with open(results_path, 'w') as f:
            json.dump(results, f)

    return {
        'name': component_id,
        'progress': 100,
        'data': results,
        'score': score,
        'colour': colour,
    }


@celery.task(bind=True)
def download_task(self, sd_uuid):
    from DataQualityTester import models
    supplied_data = models.SuppliedData.query.get_or_404(str(sd_uuid))
    url = supplied_data.source_url
    request_kwargs = {
        'headers': {'User-Agent': 'Publish What You Fund Data Quality Tester'},
        'stream': True,
    }
    try:
        resp = requests.get(url, **request_kwargs)
    except requests.exceptions.SSLError:
        resp = requests.get(url, verify=False, **request_kwargs)
    resp.raise_for_status()

    filename = resp.url.split('/')[-1].split('?')[0][:100]
    if filename == '':
        filename = 'file.xml'
    elif not filename.endswith('.xml'):
        filename += '.xml'
    filename = secure_filename(filename)
    makedirs(supplied_data.upload_dir(), exist_ok=True)

    filepath = join(supplied_data.upload_dir(), filename)
    total_length = resp.headers.get('content-length')
    if total_length:
        total_length = int(total_length)
    with open(filepath, 'wb') as f:
        dl = 0
        for block in resp.iter_content(1024):
            dl += len(block)
            f.write(block)
            if total_length:
                self.update_state(
                    state='RUNNING',
                    meta={
                        'progress': 100 * dl / total_length,
                    }
                )

    supplied_data.original_file = join(supplied_data.id, filename)
    supplied_data.downloaded = True
    db.session.add(supplied_data)
    db.session.commit()
    return {
        'progress': 100
    }
