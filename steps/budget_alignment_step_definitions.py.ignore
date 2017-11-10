import json
from os.path import join

from behave import step

from bdd_tester.exceptions import StepException


@step('at least one `{xpath_expression}` is on the {codelist} codelist')
def step_at_least_one_on_codelist(context, xpath_expression, codelist):
    vals = context.xml.xpath(xpath_expression)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(context, msg)

    codelist_path = join('codelists', '2', codelist + '.json')
    with open(codelist_path) as f:
        j = json.load(f)
    codes = [x['code'] for x in j['data']]

    for val in vals:
        if val in codes:
            assert(True)
            return

    msg = '{invalid_vals} {isare} not on the {codelist} codelist'.format(
        invalid_vals=', '.join(vals),
        isare='is' if len(vals) == 1 else 'are',
        codelist=codelist,
    )
    raise StepException(context, msg)
