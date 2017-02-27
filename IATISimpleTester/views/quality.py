from flask import render_template, jsonify, request

from IATISimpleTester import app, db, helpers
from IATISimpleTester.pagination import Pagination
from IATISimpleTester.models import SuppliedData


@app.route('/quality/<uuid:uuid>')
def package_quality(uuid):
    resp = {}
    data = SuppliedData.query.get_or_404(str(uuid))
    all_activities = helpers.load_activities_from_package(data.path_to_file())

    tests = request.args.get('tests')
    filter_ = request.args.get('filter')

    if tests in app.config['TEST_SETS']:
        test_set = app.config['TEST_SETS'].get(tests)
    else:
        test_set = app.config['TEST_SETS']['pwyf']

    # load the tests
    all_tests_list, all_filters_list = helpers.load_expressions_from_yaml(test_set['tests_file'])

    # set the filter
    current_filter = all_filters_list[0] if filter_ else None

    # single_test = helpers.select_expression(all_tests_list, request.args.get('test'))

    activities = helpers.filter_activities(all_activities, current_filter)
    activities_results, results_summary = helpers.test_activities(activities, all_tests_list)

    page = int(request.args.get('page', 1))
    offset = (page - 1) * app.config['PER_PAGE']
    pagination = Pagination(page, app.config['PER_PAGE'], len(activities))
    activities_results = activities_results[offset:offset + app.config['PER_PAGE']]

    resp['success'] = True
    resp['data'] = {
        'page': page,
        'total-activities': len(all_activities),
        'total-filtered-activities': len(activities),
        'results': activities_results,
        'results-summary': results_summary,
    }

    return jsonify(resp)
