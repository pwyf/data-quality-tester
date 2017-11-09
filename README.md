# Data Quality Tester

Test your IATI data against the Publish What You Fund Aid Transparency
Index tests.

## Installation

1. Clone the repository:

    ```shell
    git clone https://github.com/pwyf/data-quality-tester.git
    cd data-quality-tester
    ```

2. Set up a virtualenv:

    ```shell
    pyvenv .ve
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

5. Set the `FLASK_APP` environment variable:

    ```shell
    export FLASK_APP=DataQualityTester/__init__.py
    ```

    You can also append it to `.ve/bin/activate` with something like:

    ```shell
    echo -e '\nexport FLASK_APP=DataQualityTester/__init__.py' >> .ve/bin/activate
    ```

6. Set up the database:

    ```
    flask db upgrade
    ```

## Running

1. Start Redis:

    ```shell
    redis-server
    ```

2. Start a celery worker:

    ```shell
    celery worker --app DataQualityTester.celery
    ```

3. Start the webserver:

    ```shell
    flask run --with-threads
    ```
