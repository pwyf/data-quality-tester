# Data Quality Tester

Test your IATI data against the Publish What You Fund Aid Transparency
Index tests.

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/pwyf/data-quality-tester.git
    cd data-quality-tester
    ```

2. Set up a virtualenv:

    ```
    pyvenv .ve
    source .ve/bin/activate
    ```

3. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

4. Copy (and edit, if you wish) `config.py.tmpl`:

    ```
    cp config.py.tmpl config.py
    ```

5. Set up the database:

    ```
    python manage.py db upgrade
    ```

6. Run:

    ```
    python manage.py runserver
    ```
