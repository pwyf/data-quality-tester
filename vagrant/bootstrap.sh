#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

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


