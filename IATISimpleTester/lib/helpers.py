from collections import defaultdict

import yaml
from foxpath import Foxpath
from lxml import etree

from IATISimpleTester import app


# parse a {filters; tests} yaml and generate tests
def load_from_yaml(filename):
    with open(filename) as f:
        return yaml.load(f)

# given an expression list and the name of an expression,
# select it,
def select_expression(expression_list, expression_name, default_expression_name=None):
    expression_dicts = {x["id"]: x for x in expression_list}
    if expression_name not in expression_dicts:
        expression_name = default_expression_name
    return expression_name, expression_dicts.get(expression_name)

def test_activities(activities, tests_list):
    foxpath = Foxpath()
    foxtests = foxpath.load_tests(tests_list, app.config['CODELISTS'])
    activities_results = foxpath.test_activities(activities, foxtests)
    results_summary = foxpath.summarize_results(activities_results)

    return activities_results, results_summary

def group_by(groupings, results):
    results_by_grouping = defaultdict(int)
    for grouping, subgroupings in groupings.items():
        for subgrouping in subgroupings:
            if subgrouping not in results:
                continue
            results_by_grouping[grouping] += results[subgrouping]
        results_by_grouping[grouping] /= len(subgroupings)
    return results_by_grouping

def filter_activities(activities, filter_dict=None):
    if filter_dict:
        foxpath = Foxpath()
        foxtests = foxpath.load_tests([filter_dict], app.config['CODELISTS'])
        activities_results = foxpath.test_activities(activities, foxtests)

        filtered_activities = []
        for idx, activity in enumerate(activities):
            if activities_results[idx]['results'][filter_dict['name']] == 'pass':
                filtered_activities.append(activity)

        activities = filtered_activities

    return activities

def activity_to_string(activity):
    return etree.tostring(activity, pretty_print=True).strip().decode('utf-8')
