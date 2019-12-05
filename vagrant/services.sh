#!/bin/bash

cd /vagrant
source venv/bin/activate

flask assets build
flask refresh-codelists
flask db upgrade

redis-server > /dev/null 2>&1 &
celery worker --app DataQualityTester.celery -l debug > /dev/null 2>&1 &
# flask run --host 0.0.0.0 > /dev/null 2>&1 &
