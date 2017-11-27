import csv
import json
from os.path import exists, join
from urllib.parse import quote_plus, unquote_plus

from flask import abort, jsonify, redirect, request, \
                  render_template, url_for

from DataQualityTester.lib.exceptions import ActivityNotFoundException
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
    return render_template('overview.html', **context)


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
        'quote_plus': quote_plus,
    }
    return render_template('quality_by_component.html', **context)


def package_quality_by_test(uuid, component_id, test_name):
    supplied_data = SuppliedData.query.get_or_404(str(uuid))
    output_path = supplied_data.upload_dir()

    test_set_id = request.args.get('test_set')
    test_set = TestSet(test_set_id)
    component = test_set.get_component(component_id)
    test = component.get_test(unquote_plus(test_name))

    results_file = join(output_path, '{}.csv'.format(test.id))
    with open(results_file) as f:
        reader = csv.DictReader(f)
        results = [x for x in reader]

    context = {
        'component': component,
        'test': test,
        'uuid': uuid,
        'results': results,
    }
    return render_template('quality_by_test.html', **context)


def activity_quality(uuid, iati_identifier):
    supplied_data = SuppliedData.query.get_or_404(str(uuid))
    try:
        activity = supplied_data.get_activity(iati_identifier)
    except ActivityNotFoundException:
        return abort(404)

    context = {
        'uuid': uuid,
        'activity': str(activity),
        'iati_identifier': iati_identifier,
    }
    return render_template('activity.html', **context)


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
