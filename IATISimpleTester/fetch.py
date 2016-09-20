import os.path

import requests
from werkzeug.contrib.cache import SimpleCache  # MemcachedCache

from IATISimpleTester import app, config


cache = SimpleCache()
# cache = MemcachedCache(['127.0.0.1:11211'])

# cache wrapper around requests
def exec_request(url, refresh=False, *args, **kwargs):
    app.logger.info('Fetching {} ...'.format(url))
    if not refresh:
        response = cache.get(url)
        if response:
            app.logger.info('Cache hit')
            return response
    response = requests.get(url, *args, **kwargs)
    cache.set(url, response, config.CACHE_TIMEOUT)
    return response

def download_package(url, filepath):
    # download if we don't have a cached copy
    if not os.path.exists(filepath):
        r = requests.get(url, stream=True)
        with open(filepath, 'w') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

def latest_package_version(package_name, refresh=False):
    registry_url = "{registry_api}/package_show?id={package_name}".format(
        registry_api=config.REGISTRY_API_BASE_URL,
        package_name=package_name
    )
    j = exec_request(registry_url, refresh=refresh).json()
    resource = j["result"]["resources"][0]
    url = resource["url"]
    revision = resource["revision_id"]
    filename = "{package_name}-{revision}.xml".format(
        package_name=package_name,
        revision=revision
    )
    filepath = os.path.join(config.DIR_FOR_TESTING, filename)
    return url, revision, filepath
