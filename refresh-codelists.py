from os import listdir
import os.path

import yaml
from lxml import etree
import requests


# we bundle all codelists together, because we're flexible
# w.r.t. different versions of the standard.

mapping_tmpl = 'http://iatistandard.org/{version}/codelists/downloads/clv2/mapping.json'
codelist_tmpl = 'http://iatistandard.org/{version}/codelists/downloads/clv2/json/en/{codelist_name}.json'
versions = ['1.05', '2.02']

codelists = {}

for version in versions:
    print('loading mapping version-{version} ...'.format(version=version))
    version = version.replace('.', '')
    mapping = requests.get(mapping_tmpl.format(version=version)).json()
    codelist_names = {x['codelist']: None for x in mapping}.keys()
    for codelist_name in codelist_names:
        print('loading codelist {codelist_name} (version-{version}) ...'.format(codelist_name=codelist_name, version=version))
        codelist = requests.get(codelist_tmpl.format(version=version, codelist_name=codelist_name)).json()
        if codelist['attributes']['complete'] != '1':
            continue
        codes = [entry['code'] for entry in codelist['data']]
        if codelist_name not in codelists:
            codelists[codelist_name] = set()
        codelists[codelist_name].update(codes)

codelists = {codelist_name: list(codelist_set) for codelist_name, codelist_set in codelists.items()}

print('writing codeslists.yaml ...')
with open('codelists.yaml', 'w') as f:
    yaml.dump(codelists, f)
