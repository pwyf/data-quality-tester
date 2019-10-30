from os.path import join

from celery import Celery
from flask import Flask
from flask_assets import Environment as FlaskAssets, Bundle
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config.from_object('config.Config')
app.secret_key = app.config['SECRET_KEY']

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

assets = FlaskAssets(app)
assets.register('js_base', Bundle(
    join('js', 'jquery-1.12.4.js'),
    join('js', 'bootstrap-3.3.7.js'),
    filters='jsmin',
    output=join('gen', 'js.%(version)s.min.js'))
)
assets.register('js_activity', Bundle(
    join('js', 'activity.js'),
    filters='jsmin',
    output=join('gen', 'activity.%(version)s.min.js'))
)
assets.register('css_base', Bundle(
    join('css', 'bootstrap.css'),
    join('css', 'font-awesome.css'),
    join('css', 'app.css'),
    filters='cssmin',
    output=join('gen', 'css.%(version)s.min.css'))
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from DataQualityTester import commands, routes, models, views, lib # noqa
