from flask import render_template, jsonify

from IATISimpleTester import app, db
from IATISimpleTester.models import SuppliedData


@app.route('/data/<uuid>')
def explore(uuid):
    data = SuppliedData.query.get(uuid)
    print(data.id)

    return jsonify({'success': True})
