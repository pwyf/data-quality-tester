from urllib import parse

from flask import request, url_for

from IATISimpleTester import app


def url_for_other_page(page):
    args = {**request.args, **request.view_args}
    args['page'] = page
    return url_for(request.endpoint, **args)

def quote(value):
    return parse.quote(value, safe='')

def commify(value):
    return '{value:,}'.format(value=value)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['quote'] = quote
app.jinja_env.filters['commify'] = commify
