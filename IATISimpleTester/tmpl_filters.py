import urllib

from flask import request, url_for

def url_for_other_page(page):
    args = dict(request.args.items() + request.view_args.items())
    args['page'] = page
    return url_for(request.endpoint, **args)

def quote(value):
    return urllib.quote(value, safe="")
