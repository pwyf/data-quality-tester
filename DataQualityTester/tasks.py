from glob import glob
from os.path import join

from lxml import etree

from DataQualityTester import celery
from bdd_tester import bdd_tester


def _colorify(number):
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


@celery.task(bind=True)
def test_file_task(self, path_to_file, feature_path, pretty_name, output_path):
    xml = etree.parse(path_to_file)

    features = glob(join(feature_path, '*.feature'))
    feature_count = len(features)

    results = {}
    score = None
    for idx, feature in enumerate(features):
        result = bdd_tester(
            etree=xml,
            features=[feature],
            output_path=output_path
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
                'name': pretty_name,
                'progress': 100 * idx / feature_count,
                'data': results,
                'score': score,
                'colour': colour,
            }
        )

    # TODO: cache the result!
    return {
        'name': pretty_name,
        'progress': 100,
        'data': results,
        'score': score,
        'colour': colour,
    }
