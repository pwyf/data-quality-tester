from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from . import tmpl_filters


app = Flask(__name__)

app.jinja_env.globals['url_for_other_page'] = tmpl_filters.url_for_other_page
app.jinja_env.globals['quote'] = tmpl_filters.quote
app.jinja_env.filters['commify'] = tmpl_filters.commify

app.config.from_object('config.Config')
app.secret_key = app.config['SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from . import routes
