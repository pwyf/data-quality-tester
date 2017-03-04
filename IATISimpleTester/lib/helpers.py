from collections import defaultdict

import yaml
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

def group_by(groupings, results):
    results_by_grouping = defaultdict(int)
    for grouping, subgroupings in groupings.items():
        for subgrouping in subgroupings:
            if subgrouping not in results:
                continue
            results_by_grouping[grouping] += results[subgrouping]
        results_by_grouping[grouping] /= len(subgroupings)
    return results_by_grouping

def load_tests_and_filter(test_set_id):
    # load the tests
    test_set = app.config['TEST_SETS'][test_set_id]
    test_data = load_from_yaml(test_set['tests_file'])
    tests = [t for i in test_data['indicators'] for t in i['tests']]
    # set the filter
    filter_ = test_data['filter']
    return tests, filter_

def slugify(inp):
    return inp.lower().replace(' ', '-')
