# Data Quality Tester

Test your IATI data against the Publish What You Fund Aid Transparency
Index tests.

## Installation

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

    …Or you can alternatively append it to `venv/bin/activate` with something like:

    ```shell
    echo -e '\nexport FLASK_APP=DataQualityTester/__init__.py\nexport FLASK_ENV=development' >> venv/bin/activate
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
    celery --app DataQualityTester.celery worker
    ```

3. Start the webserver:

    ```shell
    flask run
    ```
