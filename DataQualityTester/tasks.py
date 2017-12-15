from glob import glob
import json
from os.path import exists, join
from os import makedirs

from bdd_tester import bdd_tester
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
def test_file_task(self, path_to_file, feature_path, component_id,
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

        step_definitions_path = join('steps', 'step_definitions.py')

        filters = [join(feature_path, '..', 'filter.feature')]
        features = glob(join(feature_path, '*.feature'))
        feature_count = len(features)
        codelists = _load_codelists()

        results = {}
        score = None
        for idx, feature in enumerate(features):
            result = bdd_tester(
                step_definitions_path,
                features,
                filters=filters,
                etree=xml,
                output_path=output_path,
                codelists=codelists,
            )
            if not result:
                continue
            results.update(result)
            score = _compute_score(results)
            if score is not None:
                colour = _colorify(score)
            else:
                colour = '#222'
            self.update_state(
                state='RUNNING',
                meta={
                    'name': component_id,
                    'progress': 100. * (idx + 1) / feature_count,
                    'data': results,
                    'score': score,
                    'colour': colour,
                }
            )
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
