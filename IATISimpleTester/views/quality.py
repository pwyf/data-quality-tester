from collections import OrderedDict

from lxml import etree
from flask import abort, flash, jsonify, redirect, render_template, request, url_for

from IATISimpleTester import app, db, helpers
from IATISimpleTester.exceptions import FileGoneException, InvalidXMLException
from IATISimpleTester.pagination import Pagination
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
    test_set_id = 'pwyf'

    # load the tests
    test_set = app.config['TEST_SETS'][test_set_id]
    test_data = helpers.load_from_yaml(test_set['tests_file'])
    tests = [t for i in test_data['indicators'] for t in i['tests']]

    # set the filter
    filter_ = None
    filtering = False
    if 'filter' in test_data:
        filter_ = test_data['filter']
        if request.args.get('filter') != 'false':
            filtering = True
        else:
            params['filter'] = 'false'

    results = data.get_results(test_set_id, filtering)

    if results:
        context = results['ctx']
        results_by_test = results['results_by_test']
    else:
        try:
            doc = etree.parse(data.path_to_file())
        except OSError:
            raise FileGoneException('Sorry – The file no longer exists.')
        except etree.XMLSyntaxError:
            raise InvalidXMLException('The file does not appear to be a valid XML file.')
        all_activities = doc.xpath('//iati-activity')

        context['total_activities'] = len(all_activities)

        if filter_:
            filtered_activities = helpers.filter_activities(all_activities, filter_)
            context['total_filtered_activities'] = len(filtered_activities)

        activities = filtered_activities if filtering else all_activities

        activities_results, results_by_test = helpers.test_activities(activities, tests)

        data.set_results(dict(ctx=context, results_by_test=results_by_test), test_set_id, filtering)

    # page = int(request.args.get('page', 1))
    # offset = (page - 1) * app.config['PER_PAGE']
    # pagination = Pagination(page, app.config['PER_PAGE'], len(activities))
    # activities_results = activities_results[offset:offset + app.config['PER_PAGE']]

    perc_by_test = OrderedDict([(k, v['pass'] / (v['pass'] + v['fail'])) for k, v in results_by_test.items() if v['pass'] + v['fail'] > 0])
    components = OrderedDict([(c['name'], c['indicators']) for c in test_data['components']])
    indicators = OrderedDict([(i['name'], [test['name'] for test in i['tests']]) for i in test_data['indicators']])
    perc_by_indicator = helpers.group_by(indicators, perc_by_test)

    component = request.args.get('component')
    if component:
        params['component'] = component
        context['results'] = OrderedDict([(k, v) for k, v in perc_by_indicator.items() if k in components[component]])
    else:
        perc_by_component = helpers.group_by(components, perc_by_indicator)
        context['results'] = perc_by_component

    return {
        'success': True,
        'data': context,
        'params': params,
    }

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

def explore(uuid):
    data = SuppliedData.query.get_or_404(str(uuid))
    return jsonify({'success': True})
