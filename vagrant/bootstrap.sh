#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

set -e

sudo echo "en_GB.UTF-8 UTF-8" >> /etc/locale.gen

sudo locale-gen

echo "**** Installing packages ****"
apt-get update
apt-get upgrade -y

apt-get install -y git python3-pip redis python3-venv python3.7 python3.7-venv libpython3.7-dev

echo "**** Setting up the application ****"
cd /vagrant
python3.7 -m venv .ve
echo -e '\nexport FLASK_APP=DataQualityTester/__init__.py\nexport FLASK_ENV=development' >> .ve/bin/activate
source .ve/bin/activate
pip install -r requirements.txt
cp config.py.tmpl config.py


