#!/usr/bin/env python
import codelists
from flask import Flask, flash, render_template, redirect, request, url_for
from foxpath import test as foxtest
import os.path
import unicodecsv
import requests

from lxml import etree


app = Flask(__name__)
app.secret_key = "super top secret key"

LISTS = codelists.CODELISTS
TESTS_FILE = 'tests.csv'
FILTERS_FILE = 'filters.csv'
UPLOAD_FOLDER = 'uploads'
REGISTRY_API_BASE_URL = "https://iatiregistry.org/api/3/action"

def download_package(url, filepath):
    # download if we don't have a cached copy
    if not os.path.exists(filepath):
        r = requests.get(url, stream=True)
        with open(filepath, 'w') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

def fetch_latest_package_version(package_name):
    registry_url = "{registry_api}/package_show?id={package_name}".format(
        registry_api=REGISTRY_API_BASE_URL,
        package_name=package_name
    )
    j = requests.get(registry_url).json()
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
    out = []
    with open(filename) as f:
        reader = unicodecsv.DictReader(f)
        for t in reader:
            out.append({
                'name': t["test_description"],
                'fn': foxtest.generate_function(t["test_name"]),
                'is_binary': foxtest.binary_test(t["test_name"]),
            })
    return out

def test_package(filepath):
    # load the tests
    all_tests = [t for t in load_expressions_from_file(TESTS_FILE)]
    all_filters = [t for t in load_expressions_from_file(FILTERS_FILE)]

    results = []
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-activity")
    for activity in activities:
        act_test = {}
        try:
            act_test["hierarchy"] = activity.xpath("@hierarchy")[0]
        except Exception:
            act_test["hierarchy"] = ""
        try:
            act_test["iati_identifier"] = activity.xpath('iati-identifier/text()')[0]
        except Exception:
            act_test["iati_identifier"] = "Unknown"
        act_test["results"] = {}
        for test_dict in all_tests:
            try:
                if test_dict["is_binary"]:
                    result = test_dict["fn"]({"activity": activity, "lists": LISTS})
                else:
                    result = test_dict["fn"](activity)
            except Exception:
                result = 2
            act_test["results"][test_dict["name"]] = foxtest.result_t(result)
        results.append(act_test)

    return results

def fetch_activity(filepath, iati_identifier):
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-identifier[text() = '" + iati_identifier + "']/..")
    return etree.tostring(activities[0])

@app.route('/')
def publishers():
    publishers = []
    j = requests.get("{registry_api}/organization_list?all_fields=true".format(
        registry_api=REGISTRY_API_BASE_URL,
    )).json()
    for publisher in j["result"]:
        publishers.append({
            "code": publisher["name"],
            "name": publisher["title"],
            "num_packages": publisher["packages"],
        })
    return render_template('publishers.html', publishers=publishers)

@app.route('/publisher/<publisher>')
def publisher(publisher):
    per_page = 20
    resources = []
    registry_tmpl = "{registry_api}/package_search?q=organization:{{publisher}}&rows={per_page}&start={{offset}}".format(
        registry_api=REGISTRY_API_BASE_URL,
        per_page=per_page,
    )
    page = int(request.args.get('page', 1))
    offset = (page - 1) * per_page
    j = requests.get(registry_tmpl.format(publisher=publisher, offset=offset)).json()
    all_result_count = j["result"]["count"]
    pages = 1 + int(float(all_result_count - 1) / per_page)
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
    args = {
        "resources": resources,
        "publisher": publisher,
        "current_page": page,
        "pages": pages,
    }
    return render_template('publisher.html', **args)

@app.route('/test/<package_name>')
def run_tests(package_name):
    # if not package_name:
    #     flash("No package name specified", 'danger')
    #     return redirect(url_for('publishers'), code=302)

    url, revision, filepath = fetch_latest_package_version(package_name)
    download_package(url, filepath)

    activities = test_package(filepath)
    args = {
        "package_name": package_name,
        "revision": revision,
        "activities": activities,
    }
    return render_template('results.html', **args)

@app.route('/activity/<package_name>/<iati_identifier>')
def view_activity(package_name, iati_identifier):
    url, revision, filepath = fetch_latest_package_version(package_name)
    download_package(url, filepath)

    activity = fetch_activity(filepath, iati_identifier).strip()
    args = {
        "package_name": package_name,
        "activity": activity,
    }
    return render_template('activity.html', **args)
