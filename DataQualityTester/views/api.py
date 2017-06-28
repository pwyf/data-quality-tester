from flask import abort, jsonify

from DataQualityTester.lib.exceptions import ActivityNotFoundException, BadUrlException, FileGoneException, InvalidXMLException, NoFormDataException
from DataQualityTester.views import quality, uploader


def package_quality_by_component(uuid, component):
    try:
        response = quality._package_quality_by_component(uuid, component)
    except (FileGoneException, InvalidXMLException) as e:
        response = {
            'success': False,
            'error': str(e),
        }
        return jsonify(response), 500
    response['data']['results'] = response['data']['results'].summary_by_test
    return jsonify(response)

def activity_quality(uuid, iati_identifier):
    try:
        response = quality._activity_quality(uuid, iati_identifier)
    except ActivityNotFoundException as e:
        response = {
            'success': False,
            'error': str(e),
        }
        return jsonify(response), 404
    response['data']['results'] = response['data']['results'].by_test
    return jsonify(response)

def upload():
    try:
        supplied_data = uploader._upload()
    except NoFormDataException:
        return abort(404)
    except BadUrlException as e:
        resp = {
            'success': False,
            'error': str(e),
        }
        return jsonify(resp)
    resp = {
        'success': True,
        'data': {
            'id': data.id,
            'original_file': data.original_file,
        }
    }
    return jsonify(resp)
