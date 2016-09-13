#!/usr/bin/env python
from flask import Flask

import tmpl_filters


app = Flask(__name__)
app.secret_key = "super top secret key"

app.jinja_env.globals['url_for_other_page'] = tmpl_filters.url_for_other_page
app.jinja_env.globals['quote'] = tmpl_filters.quote

import routes
