from DataQualityTester import app
from DataQualityTester.views import api, bdd_tester, pages, quality, uploader


@app.route('/')
def home():
    return pages.home()

# @app.route('/about')
# def about():
#     return pages.about()


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return uploader.upload()


# api
@app.route('/package/<uuid:uuid>.json')
def api_package_quality(uuid):
    return api.package_quality(uuid)


@app.route('/package/component/<component>/<uuid:uuid>.json')
def api_package_quality_by_component(uuid, component):
    return api.package_quality_by_component(uuid, component)


@app.route('/upload.json', methods=['GET', 'POST'])
def api_upload():
    return api.upload()


# @app.route('/package/<uuid:uuid>')
# def package_overview(uuid):
#     return quality.package_overview(uuid)


@app.route('/package/component/<component>/<uuid:uuid>')
def package_quality_by_component(uuid, component):
    return quality.package_quality_by_component(uuid, component)


@app.route('/package/test/<test>/<uuid:uuid>')
def package_quality_by_test(uuid, test):
    return quality.package_quality_by_test(uuid, test)


@app.route('/activity/<uuid:uuid>/<path:iati_identifier>')
def activity_quality(uuid, iati_identifier):
    return quality.activity_quality(uuid, iati_identifier)


@app.route('/package/<uuid:uuid>')
def package_overview(uuid):
    return bdd_tester.package_overview(uuid)


@app.route('/task/<uuid:task_id>')
def task_status(task_id):
    return bdd_tester.task_status(task_id)
