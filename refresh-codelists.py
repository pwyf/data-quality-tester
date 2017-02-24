from os import listdir
import os.path

import yaml
from lxml import etree


# this should also do a `git submodule update` type thing

# we bundle all codelists together, because we're flexible
# w.r.t. different versions of the standard.

codelists = {}
codelist_dirs = ['non-embedded', '1', '2']

for codelist_dir in codelist_dirs:
    codelist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'codelists', codelist_dir, 'xml')
    codelist_filenames = listdir(codelist_path)
    for codelist_filename in codelist_filenames:
        codelist_name = codelist_filename.split('.')[0]
        codelist_xml = etree.parse(os.path.join(codelist_path, codelist_filename))
        codes = [x.text for x in codelist_xml.xpath('//code')]
        if codelist_name not in codelists:
            codelists[codelist_name] = set()
        codelists[codelist_name].update(codes)

codelists = {codelist_name: list(codelist_set) for codelist_name, codelist_set in codelists.items()}

with open('codelists.yaml', 'w') as f:
    yaml.dump(codelists, f)
