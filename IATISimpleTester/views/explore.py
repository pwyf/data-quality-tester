from flask import render_template, jsonify

from IATISimpleTester import app, db
from IATISimpleTester.models import SuppliedData


@app.route('/data/<uuid:uuid>')
def explore(uuid):
    data = SuppliedData.query.get(str(uuid))
    return jsonify({'success': True})
