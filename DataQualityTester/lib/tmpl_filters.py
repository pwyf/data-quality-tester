import math as maths
from urllib import parse

from flask import request, url_for

from DataQualityTester import app
from DataQualityTester.lib import helpers


@app.template_global('url_for_other_page')
def url_for_other_page(page):
    args = request.args.copy()
    args2 = request.view_args.copy()
    args.update(args2)
    args['page'] = page
    return url_for(request.endpoint, **args)


@app.template_global('quote')
def quote(value):
    return parse.quote(value, safe='')


@app.template_filter('commify')
def commify(value):
    return '{value:,}'.format(value=value)


@app.template_filter('pluralize')
def pluralize(number, singular, plural=None):
    if number == 1:
        return singular
    else:
        if plural:
            return plural
        else:
            return singular + 's'


@app.template_global('pprint')
def pprint(explanation):
    return helpers.pprint(explanation)


@app.template_filter('ceil')
def ceil(val):
    return maths.ceil(val)


@app.template_filter('percent')
def percent(result):
    return helpers.percent(result)


@app.template_filter('colorify')
def colorify(number):
    if number is None:
        return '#222'
    # Methodology colours:
    colours = (
        ((180, 96, 122), 0),
        ((232, 152, 77), 25),
        ((248, 204, 78), 5),
        ((159, 175, 52), 75),
        ((108, 137, 178), 100),
    )
    prev_colour, prev_perc = colours[0]
    for colour, perc in colours[1:]:
        if number <= perc:
            dist = (number - prev_perc) / (perc - prev_perc)
            rgb = (int(dist * (colour[d] - prev_colour[d]) + prev_colour[d])
                   for d in range(3))
            return 'rgb({}, {}, {})'.format(*rgb)
        prev_colour = colour
        prev_perc = perc
