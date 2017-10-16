from datetime import datetime
import re

from behave import given, then

from bdd_tester.exceptions import StepException


@given('an IATI activity')
def given_activity(context):
    # this is a dummy step. It's here because
    # behave / BDD requires at least one 'given' step.
    assert(True)


@then('every `{xpath_expression}` should match the regex `{regex_str}`')
def then_every_should_match_regex(context, xpath_expression, regex_str):
    vals = context.xml.xpath(xpath_expression)
    regex = re.compile(regex_str)
    bad_vals = []
    for val in vals:
        if not bool(regex.search(val)):
            bad_vals.append(val)
    msg = '{} {} not match the regex `{}`'.format(
        ', '.join(bad_vals),
        'does' if len(bad_vals) == 1 else 'do',
        regex_str,
    )
    raise StepException(context, msg)


@given('`{xpath_expression}` is present')
def given_is_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if len(vals) > 0:
        assert(True)
    else:
        msg = '`{}` is not present'.format(
            xpath_expression,
        )
        raise StepException(context, msg)


@then('`{xpath_expression}` should not be present')
def then_should_not_be_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if len(vals) == 0:
        assert(True)
    else:
        msg = '`{}` is present, but should not be'.format(
            xpath_expression,
        )
        raise StepException(context, msg)


@given('`{xpath_expression}` is a valid date')
def given_is_valid_date(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    for val in vals:
        try:
            datetime.strptime(val, '%Y-%m-%d')
            return
        except ValueError:
            msg = '"{}" is not a valid date'.format(val)
            raise StepException(context, msg)

    msg = '`{}` not found'.format(xpath_expression)
    raise StepException(context, msg)


@then('`{xpath_expression1}` should be chronologically before ' +
      '`{xpath_expression2}`')
def then_should_be_before(context, xpath_expression1, xpath_expression2):
    less_str = context.xml.xpath(xpath_expression1)[0]
    more_str = context.xml.xpath(xpath_expression2)[0]

    less = datetime.strptime(less_str, '%Y-%m-%d').date()
    more = datetime.strptime(more_str, '%Y-%m-%d').date()

    if less > more:
        msg = '{} should be before {}, but isn\'t'.format(
            less_str,
            more_str,
        )
        raise StepException(context, msg)


@then('`{xpath_expression}` should be today, or in the past')
def then_should_be_today_or_past(context, xpath_expression):
    val = context.xml.xpath(xpath_expression)[0]
    date = datetime.strptime(val, '%Y-%m-%d').date()
    if date > context.today:
        msg = '{} should be before {}, but isn\'t'.format(
            date,
            context.today,
        )
        raise StepException(context, msg)
