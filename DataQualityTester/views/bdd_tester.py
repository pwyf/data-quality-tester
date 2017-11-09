from os.path import join

from flask import jsonify, request, render_template

from DataQualityTester.tasks import test_file_task
from DataQualityTester.models import SuppliedData, TestSet


def package_overview(uuid):
    supplied_data = SuppliedData.query.get_or_404(str(uuid))

    test_set_id = request.args.get('test_set')
    test_set = TestSet(test_set_id)

    output_path = supplied_data.upload_dir()

    task_ids = []
    for component, component_name in test_set.components:
        task = test_file_task.delay(supplied_data.path_to_file(),
                                    join(test_set.filepath, component),
                                    component_name,
                                    output_path=output_path)
        task_ids.append((component, task.id))

    context = {
        'components': test_set.components,
        'task_ids': dict(task_ids),
        'uuid': uuid,
    }
    return render_template('bdd_overview.html', **context)


def lookup_results(task_id):
    task = test_file_task.AsyncResult(str(task_id))
    if task.state == 'PENDING':
        return jsonify({
            'status': task.state,
            'data': {},
            'progress': 0,
        })
    else:
        output = {
            'status': task.state
        }
        output.update(task.info)
        return jsonify(output)
