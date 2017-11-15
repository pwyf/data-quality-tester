import json
from os.path import exists, join

from flask import jsonify, redirect, request, render_template, url_for

from DataQualityTester.tasks import test_file_task
from DataQualityTester.models import SuppliedData, TestSet


def package_overview(uuid):
    supplied_data = SuppliedData.query.get_or_404(str(uuid))

    test_set_id = request.args.get('test_set')
    test_set = TestSet(test_set_id)

    output_path = supplied_data.upload_dir()

    task_ids = []
    for component in test_set.components:
        task = test_file_task.delay(supplied_data.path_to_file(),
                                    component.filepath,
                                    component.id,
                                    output_path=output_path)
        task_ids.append((component.id, task.id))

    context = {
        'components': test_set.components,
        'task_ids': dict(task_ids),
        'uuid': uuid,
    }
    return render_template('bdd_overview.html', **context)


def package_quality_by_component(uuid, component_id):
    supplied_data = SuppliedData.query.get_or_404(str(uuid))
    output_path = supplied_data.upload_dir()

    test_set_id = request.args.get('test_set')
    test_set = TestSet(test_set_id)
    component = test_set.get_component(component_id)

    results_path = '{}.json'.format(join(output_path, component_id))
    if exists(results_path):
        with open(results_path) as f:
            results = json.load(f)
    else:
        return redirect(url_for('package_overview', uuid=uuid))

    context = {
        'component': component,
        'results': results,
        'uuid': uuid,
    }
    return render_template('bdd_quality_by_component.html', **context)


def task_status(task_id):
    task = test_file_task.AsyncResult(str(task_id))
    output = {
        'status': task.state,
    }
    if task.state == 'PENDING':
        return jsonify(output)
    else:
        output.update(task.info)
        return jsonify(output)
