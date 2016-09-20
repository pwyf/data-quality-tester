#!/usr/bin/env python
import logging
import os.path
import unicodecsv
import urllib

from flask import abort, flash, render_template, redirect, request, url_for
from foxpath import test as foxtest
from lxml import etree
import requests
from werkzeug.contrib.cache import SimpleCache  # MemcachedCache

from IATISimpleTester import app
import codelists
from pagination import Pagination


CACHE_TIMEOUT = 86400  # 24 hours
cache = SimpleCache()
# cache = MemcachedCache(['127.0.0.1:11211'])
LISTS = codelists.CODELISTS
LISTS["Agriculture"] = ["23070", "31110", "31120", "31130", "31140", "31150", "31161", "31162", "31163", "31164", "31165", "31166", "31181", "31182", "31191", "31192", "31193", "31194", "31195", "31210", "31220", "31261", "31281", "31282", "31291", "31310", "31320", "31381", "31382", "31391", "72040", "12240", "43040", "52010",]
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(CURRENT_PATH, "uploads")
TESTS_FILE = os.path.join(CURRENT_PATH, "tests.csv")
FILTERS_FILE = os.path.join(CURRENT_PATH, "filters.csv")
DEFAULT_FILTER = None
DEFAULT_TEST = None
REGISTRY_API_BASE_URL = "https://iatiregistry.org/api/3/action"
PER_PAGE = 20

def exec_request(url, refresh=False, *args, **kwargs):
    app.logger.info('Fetching {} ...'.format(url))
    if not refresh:
        response = cache.get(url)
        if response:
            app.logger.info('Cache hit')
            return response
    response = requests.get(url, *args, **kwargs)
    cache.set(url, response, CACHE_TIMEOUT)
    return response

def download_package(url, filepath):
    # download if we don't have a cached copy
    if not os.path.exists(filepath):
        r = requests.get(url, stream=True)
        with open(filepath, 'w') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

def fetch_latest_package_version(package_name, refresh=False):
    registry_url = "{registry_api}/package_show?id={package_name}".format(
        registry_api=REGISTRY_API_BASE_URL,
        package_name=package_name
    )
    j = exec_request(registry_url, refresh=refresh).json()
    resource = j["result"]["resources"][0]
    url = resource["url"]
    revision = resource["revision_id"]
    filename = "{package_name}-{revision}.xml".format(
        package_name=package_name,
        revision=revision
    )
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return url, revision, filepath

def load_expressions_from_file(filename):
    with open(filename) as f:
        reader = unicodecsv.DictReader(f)
        return [
            {
                'name': t["test_description"],
                'expression': t["test_name"],
                'fn': foxtest.generate_function(t["test_name"], LISTS),
            } for t in reader
        ]

def run_test(activity, test_dict):
    try:
        result = test_dict["fn"](activity)
    except Exception, e:
        result = 2  # ERROR
        app.logger.warning("Test error: {} ({})".format(e.message, test_dict["name"]))
    return foxtest.result_t(result)

def test_package(filepath, tests_list, filter_dict=None):
    results = []
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-activity")
    for activity in activities:
        act_test = test_activity(activity, tests_list, filter_dict)
        if not act_test:
            continue
        results.append(act_test)

    return results

def test_activity(activity, tests_list, filter_dict=None):
    if filter_dict and run_test(activity, filter_dict) == "FAIL":
        return False
    act_test = {
        "results": [run_test(activity, test_dict) for test_dict in tests_list],
    }
    act_test["results_percs"] = {
        "PASS": 0,
        "FAIL": 0,
        "ERROR": 0,
        "NOT-RELEVANT": 0,
    }
    for result in act_test["results"]:
        act_test["results_percs"][result] += 1
    for result, total in act_test["results_percs"].items():
        act_test["results_percs"][result] = 100. * total / len(tests_list)
    try:
        act_test["hierarchy"] = activity.xpath("@hierarchy")[0]
    except IndexError:
        act_test["hierarchy"] = ""
    try:
        act_test["iati_identifier"] = activity.xpath('iati-identifier/text()')[0]
    except IndexError:
        act_test["iati_identifier"] = "Unknown"
    return act_test

def fetch_activity(filepath, iati_identifier):
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-identifier[text() = '" + iati_identifier + "']/..")
    if len(activities) != 1:
        # something has gone wrong
        raise Exception
    return activities[0]


@app.route('/')
def home():
    publishers = []
    j = exec_request("{registry_api}/organization_list?all_fields=true".format(
        registry_api=REGISTRY_API_BASE_URL,
    )).json()["result"]

    search = request.args.get('q')
    if search:
        j = [x for x in j if search.lower() in x["title"].lower()]

    page = int(request.args.get('page', 1))
    offset = (page - 1) * PER_PAGE
    results = j[offset:offset + PER_PAGE]

    pagination = Pagination(page, PER_PAGE, len(j))

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
def publisher(publisher):
    resources = []
    registry_tmpl = "{registry_api}/package_search?q=organization:{{publisher}}{{search}}&rows={per_page}&start={{offset}}".format(
        registry_api=REGISTRY_API_BASE_URL,
        per_page=PER_PAGE,
    )
    page = int(request.args.get('page', 1))
    offset = (page - 1) * PER_PAGE

    search = request.args.get('q')
    searchstr = ' title:{}'.format(search) if search else ''

    j = exec_request(registry_tmpl.format(publisher=publisher, offset=offset, search=searchstr)).json()
    pagination = Pagination(page, PER_PAGE, j["result"]["count"])
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

def get_current(exp_list, current_name, default):
    exp_dicts = {x["name"]: x for x in exp_list}
    if current_name not in exp_dicts:
        current_name = default
    return current_name, exp_dicts.get(current_name)

@app.route('/test/<package_name>')
def run_tests(package_name):
    refresh = request.args.get("refresh", False)
    url, revision, filepath = fetch_latest_package_version(package_name, refresh)
    download_package(url, filepath)

    # load the tests
    all_tests_list = load_expressions_from_file(TESTS_FILE)
    current_test = get_current(all_tests_list, request.args.get('test'), DEFAULT_TEST)
    tests_to_run = all_tests_list if current_test[0] is None else [current_test[1]]

    # load and set the filter
    all_filters_list = load_expressions_from_file(FILTERS_FILE)
    current_filter = get_current(all_filters_list, request.args.get('filter'), DEFAULT_FILTER)

    activities_results = test_package(filepath, tests_to_run, current_filter[1])
    kwargs = {
        "package_name": package_name,
        "revision": revision,
        "activities_results": activities_results,

        "all_tests_list": all_tests_list,
        "tests_run_list": tests_to_run,
        "current_test": current_test,

        "all_filters_list": all_filters_list,
        "current_filter": current_filter,
    }
    return render_template('package.html', **kwargs)

@app.route('/activity/<package_name>/<iati_identifier>')
def view_activity(package_name, iati_identifier):
    refresh = request.args.get("refresh", False)
    iati_identifier = urllib.unquote(iati_identifier)
    url, revision, filepath = fetch_latest_package_version(package_name, refresh)
    download_package(url, filepath)

    try:
        activity = fetch_activity(filepath, iati_identifier)
    except:
        return abort(404)
    activity_str = etree.tostring(activity).strip()

    # load the tests
    all_tests_list = load_expressions_from_file(TESTS_FILE)
    current_test = get_current(all_tests_list, request.args.get('test'), DEFAULT_TEST)
    tests_to_run = all_tests_list if current_test[0] is None else [current_test[1]]
    # run tests
    activity_results = test_activity(activity, tests_to_run)

    kwargs = {
        "package_name": package_name,
        "activity": activity_str,
        "activity_results": activity_results,
    }
    return render_template('activity.html', **kwargs)
