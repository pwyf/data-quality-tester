import unicodecsv

from foxpath import test as foxtest
from lxml import etree

from IATISimpleTester import app, config


# parse a {filters; tests} csv and generate tests
def load_expressions_from_csvfile(filename):
    with open(filename) as f:
        reader = unicodecsv.DictReader(f)
        return [
            {
                'name': t["test_description"],
                'expression': t["test_name"],
                'fn': foxtest.generate_function(t["test_name"], config.LISTS),
            } for t in reader
        ]

# given an expression list and the name of an expression,
# select it,
def select_expression(expression_list, expression_name, default_expression_name):
    expression_dicts = {x["name"]: x for x in expression_list}
    if expression_name not in expression_dicts:
        expression_name = default_expression_name
    return expression_name, expression_dicts.get(expression_name)

# Run a test on an activity;
# Turn the result into something human-readable
def run_test(activity, test_dict):
    try:
        result = test_dict["fn"](activity)
    except Exception, e:
        result = 2  # ERROR
        app.logger.warning("Test error: {} ({})".format(e.message, test_dict["name"]))
    return foxtest.result_t(result)

def test_activity(activity, tests_list):
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

def load_and_filter_activities_from_package(filepath, filter_dict=None, offset=None):
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-activity")

    if filter_dict:
        filtered_activities = []
        for activity in activities:
            if run_test(activity, filter_dict) != "FAIL":
                filtered_activities.append(activity)
        activities = filtered_activities

    num_activities = len(activities)
    if offset is not None:
        activities = activities[offset:offset + config.PER_PAGE]

    return activities, num_activities

# fetch an activity from a file by its IATI identifier
def fetch_activity(filepath, iati_identifier):
    doc = etree.parse(filepath)
    activities = doc.xpath("//iati-identifier[text() = '" + iati_identifier + "']/..")
    if len(activities) != 1:
        # something has gone wrong
        raise Exception
    return activities[0]

def activity_to_string(activity):
    return etree.tostring(activity).strip()
