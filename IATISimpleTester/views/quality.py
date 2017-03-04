from lxml import etree
from flask import abort, flash, jsonify, redirect, render_template, request, url_for

from IATISimpleTester import app, db
from IATISimpleTester.lib import helpers
from IATISimpleTester.lib.exceptions import FileGoneException, InvalidXMLException, ActivityNotFoundException
from IATISimpleTester.models import SuppliedData, Results


def package_quality(uuid):
    try:
        response = _package_quality(uuid)
    except (FileGoneException, InvalidXMLException) as e:
        flash(str(e), 'danger')
        return redirect(url_for('home'))
    context = response['data']
    context['params'] = response['params']
    return render_template('quality.html', **context)

def _package_quality(uuid):
    params = {'uuid': str(uuid)}
    data = SuppliedData.query.get_or_404(str(uuid))

    test_set_id = app.config['DEFAULT_TEST_SET']
    filtering = request.args.get('filter') != 'false'

    tests, filter_ = helpers.load_tests_and_filter(test_set_id)

    if not filtering:
        filter_ = None

    results = data.get_results(tests, filter_)
    context = {
        'results': results,
    }

    return {
        'success': True,
        'data': context,
        'params': params,
    }

def activity_quality(uuid, iati_identifier):
    try:
        response = _activity_quality(uuid, iati_identifier)
    except ActivityNotFoundException:
        return abort(404)
    context = response['data']
    context['params'] = response['params']
    return render_template('activity.html', **context)

def _activity_quality(uuid, iati_identifier):
    params = {
        'uuid': str(uuid),
        'iati_identifier': iati_identifier,
    }
    data = SuppliedData.query.get_or_404(str(uuid))

    test_set_id = app.config['DEFAULT_TEST_SET']
    filtering = request.args.get('filter') != 'false'

    tests, filter_ = helpers.load_tests_and_filter(test_set_id)

    activity = data.get_activity(iati_identifier)
    results = data.get_results(tests, filter_)

    context = {
        'results': results,
        'activity': str(activity),
    }

    return {
        'success': True,
        'data': context,
        'params': params,
    }

def explore(uuid):
    data = SuppliedData.query.get_or_404(str(uuid))
    return jsonify({'success': True})
