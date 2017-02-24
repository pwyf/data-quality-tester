import os.path

import requests
from werkzeug.contrib.cache import MemcachedCache

from IATISimpleTester import app


# using memcache for caching
cache = MemcachedCache(['127.0.0.1:11211'])

# cache wrapper around requests
def exec_request(url, refresh=False, *args, **kwargs):
    app.logger.info('Fetching {} ...'.format(url))
    if not refresh:
        response = cache.get(url)
        if response:
            app.logger.info('Cache hit')
            return response
    response = requests.get(url, *args, **kwargs)
    cache.set(url, response, app.config['CACHE_TIMEOUT'])
    return response

def download_resource(url, package_name):
    filename = "{package_name}.xml".format(
        package_name=package_name
    )
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # download if we don't have a cached copy
    if not os.path.exists(filepath):
        from_cache = False
        try:
            r = requests.get(url, stream=True)
        except requests.exceptions.SSLError:
            r = requests.get(url, verify=False, stream=True)
        if r.status_code != 200:
            raise IOError  # sort of
        with open(filepath, 'w') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    else:
        from_cache = True
    return filepath, from_cache

def get_package_url(package_name, refresh=False):
    registry_url = "{registry_api}/package_show?id={package_name}".format(
        registry_api=app.config['REGISTRY_API_BASE_URL'],
        package_name=package_name
    )
    j = exec_request(registry_url, refresh=refresh).json()
    resource = j["result"]["resources"][0]
    url = resource["url"]
    return url

def get_publishers():
    r = exec_request("{registry_api}/organization_list?all_fields=true".format(
        registry_api=app.config['REGISTRY_API_BASE_URL'],
    ))
    return r.json()["result"]

def get_publisher_packages(publisher, **kwargs):
    registry_tmpl = "{registry_api}/package_search?q=organization:{publisher}{search}&rows={per_page}&start={offset}"

    search = kwargs.get('search', '')
    page = kwargs.get('page', 1)
    per_page = kwargs.get('per_page', app.config['PER_PAGE'])

    offset = (page - 1) * app.config['PER_PAGE']
    r = exec_request(registry_tmpl.format(
        registry_api=app.config['REGISTRY_API_BASE_URL'],
        publisher=publisher,
        search=search,
        per_page=per_page,
        offset=offset,
    ))
    return r.json()["result"]
