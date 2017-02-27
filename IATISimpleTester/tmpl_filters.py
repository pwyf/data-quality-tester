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
