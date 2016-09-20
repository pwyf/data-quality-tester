import unicodecsv

from foxpath import test as foxtest

from IATISimpleTester import config


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

def get_current(exp_list, current_name, default):
    exp_dicts = {x["name"]: x for x in exp_list}
    if current_name not in exp_dicts:
        current_name = default
    return current_name, exp_dicts.get(current_name)
