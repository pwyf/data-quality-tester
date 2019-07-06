from datetime import datetime, timedelta
from os.path import join
import shutil

import click
import requests

from DataQualityTester import app
from DataQualityTester.models import SuppliedData


@app.cli.command()
@click.option('-a', '--all', 'flush_all', is_flag=True)
def flush_data(flush_all):
    '''
    Delete files that are older than 7 days
    (or all files, using the --all switch)
    '''
    if flush_all:
        old_data = SuppliedData.query.all()
    else:
        old_data = SuppliedData.query.filter(
            SuppliedData.created <= datetime.utcnow() - timedelta(days=7))
    for supplied_data in old_data:
        try:
            shutil.rmtree(supplied_data.upload_dir())
        except FileNotFoundError:
            continue


@app.cli.command()
def refresh_codelists():
    '''
    Command to fetch IATI codelists in json format and dump them
    for use in some of the tests.

    Usage: flask refresh_codelists
    '''
    versions = (
        {
            'iati_version': '105',
            'codelist_version': 'clv2',
        }, {
            'iati_version': '202',
            'codelist_version': 'clv3',
        },
    )
    all_codelists_tmpl = 'http://iatistandard.org/{iati_version}/' + \
        'codelists/downloads/{codelist_version}/codelists.json'
    codelist_tmpl = 'http://iatistandard.org/{iati_version}/' + \
        'codelists/downloads/{codelist_version}/json/en/{codelist_name}.json'
    codelists_path = join(app.config.get('CURRENT_PATH'), 'codelists')
    for version in versions:
        codelist_path = join(codelists_path, version['iati_version'][0])
        all_codelists_url = all_codelists_tmpl.format(**version)
        print('fetching {}'.format(all_codelists_url))
        codelist_names = requests.get(all_codelists_url).json()
        for codelist_name in codelist_names:
            codelist_url = codelist_tmpl.format(codelist_name=codelist_name,
                                                **version)
            print('fetching {}'.format(codelist_url))
            r = requests.get(codelist_url)
            with open(join(codelist_path, codelist_name + '.json'), 'w') as f:
                f.write(r.text)
