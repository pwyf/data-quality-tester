#!/usr/bin/env python
import logging
import os.path
import unicodecsv

from flask import Flask, flash, render_template, redirect, request, url_for
from foxpath import test as foxtest
from lxml import etree
import requests
from werkzeug.contrib.cache import SimpleCache  # MemcachedCache

import codelists
from pagination import Pagination


app = Flask(__name__)
app.secret_key = "super top secret key"
CACHE_TIMEOUT = 86400  # 24 hours

cache = SimpleCache()
# cache = MemcachedCache(['127.0.0.1:11211'])

LISTS = codelists.CODELISTS
LISTS["Agriculture"] = ["31110", "31120", "31130", "31140", "31150", "31161", "31162", "31163", "31164", "31165", "31166", "31181", "31182", "31191", "31192", "31193", "31194", "31195", "31210", "31220", "31261", "31281", "31282", "31291", "31310", "31320", "31381", "31382", "31391", "72040", "12240", "43040", "52010",]
TESTS_FILE = "tests.csv"
FILTERS_FILE = "filters.csv"
DEFAULT_FILTER = None
UPLOAD_FOLDER = "uploads"
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
        return {
            t["test_description"]: {
                'name': t["test_description"],
                'fn': foxtest.generate_function(t["test_name"]),
                'is_binary': foxtest.binary_test(t["test_name"]),
            } for t in reader
        }

def test_activity(activity, test_dict):
    try:
        if test_dict["is_binary"]:
            result = test_dict["fn"]({"activity": activity, "lists": LISTS})
        else:
            result = test_dict["fn"](activity)
    except Exception:
        result = 2  # ERROR
    return foxtest.result_t(result)

def test_package(filepath, tests_suite, filter_dict=None):
    results = []
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-activity")
    for activity in activities:
        if filter_dict and test_activity(activity, filter_dict) == "FAIL":
            continue
        act_test = {
            "results": {test_dict["name"]: test_activity(activity, test_dict) for test_dict in tests_suite},
        }
        try:
            act_test["hierarchy"] = activity.xpath("@hierarchy")[0]
        except IndexError:
            act_test["hierarchy"] = ""
        try:
            act_test["iati_identifier"] = activity.xpath('iati-identifier/text()')[0]
        except IndexError:
            act_test["iati_identifier"] = "Unknown"

        results.append(act_test)

    return results

def fetch_activity(filepath, iati_identifier):
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-identifier[text() = '" + iati_identifier + "']/..")
    return etree.tostring(activities[0])

def url_for_other_page(page):
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

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
    registry_tmpl = "{registry_api}/package_search?q=organization:{{publisher}}&rows={per_page}&start={{offset}}".format(
        registry_api=REGISTRY_API_BASE_URL,
        per_page=PER_PAGE,
    )
    page = int(request.args.get('page', 1))
    offset = (page - 1) * PER_PAGE

    j = exec_request(registry_tmpl.format(publisher=publisher, offset=offset)).json()
    pagination = Pagination(page, PER_PAGE, j["result"]["count"])
    for result in j["result"]["results"]:
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

@app.route('/test/<package_name>')
def run_tests(package_name):
    refresh = request.args.get("refresh", False)
    url, revision, filepath = fetch_latest_package_version(package_name, refresh)
    download_package(url, filepath)

    # load the tests
    tests_suite = load_expressions_from_file(TESTS_FILE).values()

    # load and set the filter
    filters_suite = load_expressions_from_file(FILTERS_FILE)
    current_filter = request.args.get('filter', DEFAULT_FILTER)
    current_filter = DEFAULT_FILTER if current_filter not in filters_suite else current_filter
    filter_dict = filters_suite.get(current_filter)

    activities = test_package(filepath, tests_suite, filter_dict)
    kwargs = {
        "package_name": package_name,
        "revision": revision,
        "activities": activities,
        "current_filter": current_filter,
    }
    return render_template('results.html', **kwargs)

@app.route('/activity/<package_name>/<iati_identifier>')
def view_activity(package_name, iati_identifier):
    refresh = request.args.get("refresh", False)
    url, revision, filepath = fetch_latest_package_version(package_name, refresh)
    download_package(url, filepath)

    activity = fetch_activity(filepath, iati_identifier).strip()
    kwargs = {
        "package_name": package_name,
        "activity": activity,
    }
    return render_template('activity.html', **kwargs)
