import json
from os.path import exists, join

from flask import abort, jsonify, request
from bdd_tester import bdd_tester

from DataQualityTester.models import SuppliedData, TestSet


def test_feature(component, indicator):
    uuid = request.args.get('uuid', '')
    supplied_data = SuppliedData.query.get_or_404(uuid)

    test_set_id = request.args.get('test_set')
    test_set = TestSet(test_set_id)

    feature_path = join(test_set.filepath, component, indicator + '.feature')
    if not exists(feature_path):
        print(feature_path)
        return abort(404)

    output_path = supplied_data.upload_dir()

    results = bdd_tester(supplied_data.path_to_file(), [feature_path], output_path=output_path)

    return jsonify(results)
