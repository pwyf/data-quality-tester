import logging
import os.path
from urllib import parse

from flask import abort, flash, render_template, redirect, request, url_for

from IATISimpleTester import app, fetch, helpers
from .pagination import Pagination


@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/publishers')
def publishers():
    publishers = []
    j = fetch.get_publishers()

    search = request.args.get('q')
    if search:
        j = [x for x in j if search.lower() in x["title"].lower()]

    results = sorted(j, key=lambda x: int(x["package_count"]), reverse=True)

    page = int(request.args.get('page', 1))
    offset = (page - 1) * app.config['PER_PAGE']
    results = results[offset:offset + app.config['PER_PAGE']]

    pagination = Pagination(page, app.config['PER_PAGE'], len(j))

    for publisher in results:
        publishers.append({
            "code": publisher["name"],
            "name": publisher["title"],
            "num_packages": int(publisher["package_count"]),
        })

    kwargs = {
        "pagination": pagination,
        "publishers": publishers,
    }
    return render_template('publishers.html', **kwargs)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/publisher/<publisher>')
def publisher(publisher):
    resources = []
    page = int(request.args.get('page', 1))

    search = request.args.get('q')
    searchstr = ' title:{}'.format(search) if search else ''

    j = fetch.get_publisher_packages(publisher, page=page, search=searchstr)
    pagination = Pagination(page, app.config['PER_PAGE'], j["count"])
    for result in j["results"]:
        if result["num_resources"] == 0:
            continue
        filetype = [extra["value"] for extra in result["extras"] if extra["key"] == "filetype"][0]
        for resource in result["resources"]:
            resources.append({
                "title": result["title"],
                "url": resource["url"],
                "package_name": result["name"],
                "revision": resource["revision_id"],
                "filetype": filetype,
            })
    kwargs = {
        "resources": resources,
        "publisher": publisher,
        "pagination": pagination,
    }
    return render_template('publisher.html', **kwargs)

@app.route('/package/<filename>.xml')
@app.route('/package/<package_name>')
def package(package_name=None, filename=None):
    if filename:
        package_name = filename + '.xml'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], package_name)
    else:
        refresh = request.args.get("refresh", False)
        url = fetch.get_package_url(package_name, refresh)
        filepath, _ = fetch.download_resource(url, package_name)

    groupings = app.config['TEST_GROUPINGS']
    all_tests_list = {}
    all_filters_list = {}
    current_filter = {}
    activities = {}
    num_activities = {}
    activities_results = {}
    results_summary = {}
    num_filtered_activities = {}
    all_activities = helpers.load_activities_from_package(filepath)
    num_activities = len(all_activities)
    for grouping in groupings:
        # load the tests
        id_ = grouping['name']
        all_tests_list[id_], all_filters_list[id_] = helpers.load_expressions_from_yaml(grouping['tests_file'])
        # single_test = helpers.select_expression(all_tests_list, request.args.get('test'))

        # page = int(request.args.get('page', 1))
        # offset = (page - 1) * app.config['PER_PAGE']

        # set the filter
        current_filter[id_] = all_filters_list[id_][0] if all_filters_list[id_] else None

        activities[id_] = helpers.filter_activities(all_activities, current_filter[id_])
        activities_results[id_], results_summary[id_] = helpers.test_activities(activities[id_], all_tests_list[id_])

        num_filtered_activities[id_] = len(activities)
        # pagination = Pagination(page, app.config['PER_PAGE'], num_activities)

        # activities_results[id_] = activities_results[offset:offset + app.config['PER_PAGE']]

    kwargs = {
        "groupings": groupings,
        "package_name": package_name,

        "activities_results": activities_results,
        "results_summary": results_summary,
        "num_activities": num_activities,

        "all_tests_list": all_tests_list,
        # "current_test": single_test,
        "current_filter": current_filter,
    }
    return render_template('package.html', **kwargs)

@app.route('/activity/<filename>.xml/<iati_identifier>')
@app.route('/activity/<package_name>/<iati_identifier>')
def activity(iati_identifier, filename=None, package_name=None):
    refresh = request.args.get("refresh", False)
    if filename:
        package_name = filename + '.xml'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], package_name)
    else:
        iati_identifier = parse.unquote(iati_identifier)
        url = fetch.get_package_url(package_name, refresh)
        filepath, _ = fetch.download_resource(url, package_name)

    try:
        activity = helpers.fetch_activity(filepath, iati_identifier)
    except:
        return abort(404)
    activity_str = helpers.activity_to_string(activity)

    # load the tests
    all_tests_list, all_filters_list = helpers.load_expressions_from_yaml(app.config['TESTS_FILE'])
    # run tests
    activities_results, _ = helpers.test_activities([activity], all_tests_list)
    activity_results = activities_results[0]

    kwargs = {
        "package_name": package_name,
        "activity": activity_str,
        "activity_results": activity_results,

        "all_tests_list": all_tests_list,
    }
    return render_template('activity.html', **kwargs)
