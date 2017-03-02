from urllib import parse

from flask import request, url_for

from IATISimpleTester import app


@app.template_global('url_for_other_page')
def url_for_other_page(page):
    args = {**request.args, **request.view_args}
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

@app.template_filter('colorify')
def colorify(number):
    '''
    colorify(0)  # returns 255, 0, 0
    colorify(0.5)  # returns 255, 255, 0
    colorify(1)  # returns 0, 255, 0

    TODO: totaliser colours:
    b4607a 0%
    e8984d 25%
    f8cc4e 50%
    9faf34 75%
    6c89b2 100%
    '''
    b = 0
    if number < 0.5:
        r = 255
        g = int(number / 0.5 * 255)
    else:
        r = int(255 * 2 * (1 - number))
        g = 255
    return 'rgb({r}, {g}, {b})'.format(r=r, g=g, b=b)
