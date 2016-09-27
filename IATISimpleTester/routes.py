#!/usr/bin/env python
import logging
import os.path
import urllib

from flask import abort, flash, render_template, redirect, request, url_for

from IATISimpleTester import app, config, fetch, helpers
from IATISimpleTester.pagination import Pagination


@app.route('/')
def show_home():
    publishers = []
    j = fetch.exec_request("{registry_api}/organization_list?all_fields=true".format(
        registry_api=config.REGISTRY_API_BASE_URL,
    )).json()["result"]

    search = request.args.get('q')
    if search:
        j = [x for x in j if search.lower() in x["title"].lower()]

    page = int(request.args.get('page', 1))
    offset = (page - 1) * config.PER_PAGE
    results = j[offset:offset + config.PER_PAGE]

    pagination = Pagination(page, config.PER_PAGE, len(j))

    for publisher in results:
        publishers.append({
            "code": publisher["name"],
            "name": publisher["title"],
            "num_packages": publisher["packages"],
        })

    kwargs = {
        "pagination": pagination,
        "publishers": publishers,
    }
    return render_template('publishers.html', **kwargs)

@app.route('/publisher/<publisher>')
def show_publisher(publisher):
    resources = []
    registry_tmpl = "{registry_api}/package_search?q=organization:{{publisher}}{{search}}&rows={per_page}&start={{offset}}".format(
        registry_api=config.REGISTRY_API_BASE_URL,
        per_page=config.PER_PAGE,
    )
    page = int(request.args.get('page', 1))
    offset = (page - 1) * config.PER_PAGE

    search = request.args.get('q')
    searchstr = ' title:{}'.format(search) if search else ''

    j = fetch.exec_request(registry_tmpl.format(publisher=publisher, offset=offset, search=searchstr)).json()
    pagination = Pagination(page, config.PER_PAGE, j["result"]["count"])
    for result in j["result"]["results"]:
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

@app.route('/package/<package_name>')
def show_package(package_name):
    refresh = request.args.get("refresh", False)
    url, revision, filepath = fetch.latest_package_version(package_name, refresh)
    fetch.download_package(url, filepath)

    # load the tests
    all_tests_list = helpers.load_expressions_from_csvfile(config.TESTS_FILE)
    current_test = helpers.select_expression(all_tests_list, request.args.get('test'), config.DEFAULT_TEST)
    tests_to_run = all_tests_list if current_test[0] is None else [current_test[1]]

    # load and set the filter
    all_filters_list = helpers.load_expressions_from_csvfile(config.FILTERS_FILE)
    current_filter = helpers.select_expression(all_filters_list, request.args.get('filter'), config.DEFAULT_FILTER)

    page = int(request.args.get('page', 1))
    offset = (page - 1) * config.PER_PAGE

    activities, num_activities = helpers.load_and_filter_activities_from_package(filepath, current_filter[1], offset=offset)
    activities_results = [helpers.test_activity(activity, tests_to_run) for activity in activities]

    pagination = Pagination(page, config.PER_PAGE, num_activities)

    kwargs = {
        "package_name": package_name,
        "revision": revision,
        "activities_results": activities_results,

        "all_tests_list": all_tests_list,
        "tests_run_list": tests_to_run,
        "current_test": current_test,

        "all_filters_list": all_filters_list,
        "current_filter": current_filter,

        "pagination": pagination,
    }
    return render_template('package.html', **kwargs)

@app.route('/activity/<package_name>/<iati_identifier>')
def show_activity(package_name, iati_identifier):
    refresh = request.args.get("refresh", False)
    iati_identifier = urllib.unquote(iati_identifier)
    url, revision, filepath = fetch.latest_package_version(package_name, refresh)
    fetch.download_package(url, filepath)

    try:
        activity = helpers.fetch_activity(filepath, iati_identifier)
    except:
        return abort(404)
    activity_str = helpers.activity_to_string(activity)

    # load the tests
    all_tests_list = helpers.load_expressions_from_csvfile(config.TESTS_FILE)
    current_test = helpers.select_expression(all_tests_list, request.args.get('test'), config.DEFAULT_TEST)
    tests_to_run = all_tests_list if current_test[0] is None else [current_test[1]]
    # run tests
    activity_results = helpers.test_activity(activity, tests_to_run)

    kwargs = {
        "package_name": package_name,
        "activity": activity_str,
        "activity_results": activity_results,

        "all_tests_list": all_tests_list,
        "tests_run_list": tests_to_run,
        "current_test": current_test,
    }
    return render_template('activity.html', **kwargs)
