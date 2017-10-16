from flask import jsonify, request, url_for

from DataQualityTester.tasks import test_file
from DataQualityTester.models import SuppliedData, TestSet


def test_features(uuid):
    supplied_data = SuppliedData.query.get_or_404(str(uuid))

    test_set_id = request.args.get('test_set')
    test_set = TestSet(test_set_id)

    output_path = supplied_data.upload_dir()

    task = test_file.delay(supplied_data.path_to_file(),
                           test_set.filepath,
                           output_path=output_path)

    result_url = url_for('test_results', task_id=task.id, _external=True)
    return jsonify({'url': result_url}), 202, {'Location': result_url}


def test_results(task_id):
    task = test_file.AsyncResult(str(task_id))
    if task.state == 'PENDING':
        return jsonify({
            'status': task.state,
            'results': {},
            'progress': 0,
        })
    else:
        return jsonify({
            'status': task.state,
            'results': task.info.get('results'),
            'progress': task.info.get('progress'),
        })
