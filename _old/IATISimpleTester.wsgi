#!/usr/bin/env python
import logging, sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/home/tracker/iati-simple-tester/pyenv/lib/python2.7/site-packages')
sys.path.insert(0, '/home/tracker/iati-simple-tester')
from IATISimpleTester import app as application
