from collections import defaultdict
import re

from lxml import etree

from IATISimpleTester import app


# given an expression list and the name of an expression,
# select it,
def select_expression(expression_list, expression_name, default_expression_name=None):
    expression_dicts = {x["id"]: x for x in expression_list}
    if expression_name not in expression_dicts:
        expression_name = default_expression_name
    return expression_name, expression_dicts.get(expression_name)

def slugify(inp):
    return inp.lower().replace(' ', '-')

def pprint(explanation):
    print(explanation)
    explanation = explanation.strip().capitalize().replace('\n', '<br>') + '.'
    return re.sub(r'`([^`]*)`', r'<code>\1</code>', explanation)
