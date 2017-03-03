from collections import OrderedDict

from lxml import etree
from flask import abort, flash, jsonify, redirect, render_template, request, url_for

from IATISimpleTester import app, db
from IATISimpleTester.lib import helpers
from IATISimpleTester.lib.exceptions import FileGoneException, InvalidXMLException, ActivityNotFoundException
from IATISimpleTester.models import SuppliedData


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
    data = SuppliedData.query.get_or_404(str(uuid))

    context = {}
    params = {'uuid': str(uuid)}

    # hardcode a testset to use
    test_set_id = app.config['DEFAULT_TEST_SET']
    filtering = request.args.get('filter') != 'false'

    results = data.get_results(test_set_id, filtering)
    context = {
        'total_activities': results.total_activities,
        'total_filtered_activities': results.total_filtered_activities,
    }

    perc_by_test = OrderedDict([(k, v['pass'] / (v['pass'] + v['fail'])) for k, v in results.by_test.items() if v['pass'] + v['fail'] > 0])
    context['results'] = perc_by_test

    return {
        'success': True,
        'data': context,
        'params': params,
    }

def activity_quality(uuid, iati_identifier):
    data = SuppliedData.query.get_or_404(str(uuid))
    try:
        activity = data.parse(iati_identifier)
    except ActivityNotFoundException:
        return abort(404)

    context = {
        'activity': helpers.activity_to_string(activity),
        'uuid': uuid,
    }
    return render_template('activity.html', **context)

def explore(uuid):
    data = SuppliedData.query.get_or_404(str(uuid))
    return jsonify({'success': True})
