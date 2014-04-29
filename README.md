# Simple IATI tester

This small application makes use of the foxpath framework used in the
Aid Transparency Index. The aim is to output a CSV file containing pass/fail
for each activity for a given dictionary of tests.

## License

Copyright (C) 2014, Mark Brough, Publish What You Fund. AGPL v3.0 licensed.

## Get started

1. Make sure you have some basic Python dependencies installed:

        sudo apt-get install python-dev libxml2-dev libxslt-dev

2. Set up a virtualenv and activate: 

        virtualenv ./pyenv
        source ./pyenv/bin/activate

3. Install the requirements:

        pip install -r requirements.txt

4. Copy and edit config.py.tmpl:

        cp config.py.tmpl config.py
        vim config.py

5. Run the script:

        python run.py
