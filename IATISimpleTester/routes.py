from IATISimpleTester import app
from IATISimpleTester.views import api, pages, quality, uploader


@app.route('/')
def home():
    return pages.home()

@app.route('/about')
def about():
    return pages.about()

@app.route('/data/<uuid:uuid>')
def explore(uuid):
    return quality.explore(uuid)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return uploader.upload()

# api
@app.route('/quality/<uuid:uuid>.json')
def api_package_quality(uuid):
    return api.package_quality(uuid)

@app.route('/quality/<uuid:uuid>/<path:iati_identifier>.json')
def api_activity_quality(uuid, iati_identifier):
    return api.activity_quality(uuid, iati_identifier)

@app.route('/upload.json', methods=['GET', 'POST'])
def api_upload():
    return api.upload()

# data quality
@app.route('/quality/<uuid:uuid>')
def package_quality(uuid):
    return quality.package_quality(uuid)

@app.route('/quality/<uuid:uuid>/<path:iati_identifier>')
def activity_quality(uuid, iati_identifier):
    return quality.activity_quality(uuid, iati_identifier)
