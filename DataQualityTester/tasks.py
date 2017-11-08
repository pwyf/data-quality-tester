from glob import glob
from os.path import join

from DataQualityTester import celery
from bdd_tester import bdd_tester


@celery.task(bind=True)
def test_file(self, path_to_file, feature_path, output_path):
    features = glob(join(feature_path, '**', '*.feature'), recursive=True)
    feature_count = len(features)

    overall_results = {}
    for idx, feature in enumerate(features):
        result = bdd_tester(
            filepath=path_to_file,
            features=[feature],
            output_path=output_path
        )
        overall_results.update(result)
        self.update_state(
            state='RUNNING',
            meta={
                'progress': 100 * idx / feature_count,
                'results': overall_results,
            }
        )

    return {'progress': 100, 'results': overall_results}
