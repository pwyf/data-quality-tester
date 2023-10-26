# Data Quality Tester

Test your IATI data against the Publish What You Fund Aid Transparency
Index tests.

## Installation option 1: using Vagrant

See the [`vagrant/README.md`](vagrant/README.md) file for details.

## Installation option 2: without Vagrant

1. Clone the repository:

    ```shell
    git clone --recursive https://github.com/pwyf/data-quality-tester.git
    cd data-quality-tester
    ```

2. Set up a virtualenv:

    ```shell
    python3.7 -m venv .ve
    source .ve/bin/activate
    ```

3. Install dependencies:

    ```shell
    pip install -r requirements.txt
    ```

4. Copy (and edit, if you wish) `config.py.tmpl`:

    ```shell
    cp config.py.tmpl config.py
    ```

5. Set the environment variables:

    ```shell
    export FLASK_APP=DataQualityTester/__init__.py
    export FLASK_ENV=development
    ```

    …Or you can alternatively append it to `.ve/bin/activate` with something like:

    ```shell
    echo -e '\nexport FLASK_APP=DataQualityTester/__init__.py\nexport FLASK_ENV=development' >> .ve/bin/activate
    ```

6. Build the assets, download codelists, and set up the database:

   ```
   flask assets build
   flask refresh-codelists
   flask db upgrade
   ```

## Running (without Vagrant)

1. Start a Redis server:

   If you have a native install of redis server:

   ```shell
   redis-server
   ```

   Alternatively, you can also run it in docker:

   ```shell
   docker run -d -p 6379:6379 redis
   ```

2. Start a celery worker:

    ```shell
    celery --app DataQualityTester.celery worker
    ```

3. Start the webserver:

    ```shell
    flask run
    ```
