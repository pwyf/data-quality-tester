# Simple IATI tester

This small application makes use of the foxpath framework used in the
Aid Transparency Index. The aim is to output a CSV file containing pass/fail
for each activity for a given dictionary of tests.

## License: AGPL v3

Copyright (C) 2014, Mark Brough, Publish What You Fund. AGPL v3.0 licensed.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
