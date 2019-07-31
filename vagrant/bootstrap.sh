#!/bin/bash

set -e

sudo echo "en_GB.UTF-8 UTF-8" >> /etc/locale.gen

sudo locale-gen

echo "**** Installing packages ****"
apt-get update
apt-get upgrade -y

apt-get install -y git python3-pip redis python3-venv

echo "**** Setting up the application ****"
cd /vagrant
python3 -m venv venv
echo -e '\nexport FLASK_APP=DataQualityTester/__init__.py\nexport FLASK_ENV=development' >> venv/bin/activate
source venv/bin/activate
pip install -r requirements.txt
cp config.py.tmpl config.py

echo "**** Build the assets and run the server ****"
flask assets build

echo "**** Retrieve all of the codelists from IATI register ****"
flask refresh-codelists

echo "**** Set up the databases ****"
flask db upgrade

echo "**** Start redis ****"
redis-server > /dev/null 2>&1 &

echo "**** Start celery ****"
celery worker --app DataQualityTester.celery -l debug &


