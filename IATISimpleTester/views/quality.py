from lxml import etree

from flask import abort, flash, redirect, render_template, jsonify, request, url_for

from IATISimpleTester import app, db, helpers
from IATISimpleTester.pagination import Pagination
from IATISimpleTester.models import SuppliedData


@app.route('/quality/<uuid:uuid>.json')
@app.route('/quality/<uuid:uuid>')
def package_quality(uuid):
    response, status = _package_quality(uuid)
    if request.path.endswith('.json'):
        return jsonify(response), status
    if status != 200:
        flash(response['error'], 'danger')
        return redirect(url_for('home'))
    return render_template('quality.html', **response['data'])

def _package_quality(uuid):
    data = SuppliedData.query.get_or_404(str(uuid))

    try:
        doc = etree.parse(data.path_to_file())
    except OSError:
        return {
            'success': False,
            'error': 'Sorry – The file no longer exists',
        }, 500
    except etree.XMLSyntaxError:
        return {
            'success': False,
            'error': 'The file appears to be invalid',
        }, 500
    all_activities = doc.xpath('//iati-activity')

    tests = request.args.get('tests')
    filter_ = request.args.get('filter')

    if tests in app.config['TEST_SETS']:
        test_set = app.config['TEST_SETS'].get(tests)
    else:
        test_set = app.config['TEST_SETS']['pwyf']

    # load the tests
    all_tests_list, all_filters_list = helpers.load_expressions_from_yaml(test_set['tests_file'])

    # set the filter
    current_filter = all_filters_list[0] #  if filter_ else None

    # single_test = helpers.select_expression(all_tests_list, request.args.get('test'))

    activities = helpers.filter_activities(all_activities, current_filter)
    activities_results, results_summary = helpers.test_activities(activities, all_tests_list)

    page = int(request.args.get('page', 1))
    offset = (page - 1) * app.config['PER_PAGE']
    pagination = Pagination(page, app.config['PER_PAGE'], len(activities))
    activities_results = activities_results[offset:offset + app.config['PER_PAGE']]

    context = {
        'page': page,
        'total-activities': len(all_activities),
        'total-filtered-activities': len(activities),
        'results': activities_results,
        'results-summary': results_summary,
    }

    return {
        'success': True,
        'data': context,
    }, 200

@app.route('/quality/<uuid:uuid>/<path:iati_identifier>')
def activity_quality(uuid, iati_identifier):
    data = SuppliedData.query.get_or_404(str(uuid))
    try:
        doc = etree.parse(data.path_to_file())
    except OSError:
        return {
            'success': False,
            'error': 'Sorry – The file no longer exists',
        }, 500
    except etree.XMLSyntaxError:
        return {
            'success': False,
            'error': 'The file appears to be invalid',
        }, 500

    activity = helpers.fetch_activity(doc, iati_identifier)
    if not activity:
        return abort(404)
    context = {
        'activity': helpers.activity_to_string(activity),
        'uuid': uuid,
    }
    return render_template('activity.html', **context)
