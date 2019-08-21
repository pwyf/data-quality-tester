# Initialise the vagrant box

```
vagrant up
```

This will create the box and run all of the required services including Redis, Celery, and the Flask server. Assuming this completes successfully then you can visit:

localhost:5000

## How to run any of the steps manually

``` bash
vagrant ssh

cd /vagrant

source venv/bin/activate

flask assets build

flask refresh-codelists

flask db upgrade

redis-server > /dev/null 2>&1 &

celery worker --app DataQualityTester.celery -l debug > /dev/null 2>&1 &
```

## Run webservice with vagrant

webservice (flask uses port 5000 by default, this is opened on the vagrant box):

``` bash
flask run --host 0.0.0.0
```