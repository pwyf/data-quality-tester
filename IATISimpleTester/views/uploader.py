import os.path

from flask import abort, request, jsonify, redirect, url_for

from IATISimpleTester import app, db
from IATISimpleTester.models import SuppliedData


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    source_url = request.args.get('source_url')
    file = request.files.get('file')
    raw_text = request.args.get('paste')
    form_name = None

    if source_url:
        form_name = 'url_form'
    elif raw_text:
        form_name = 'text_form'
    elif file:
        form_name = 'upload_form'

    if not form_name:
        return abort(404)

    data = SuppliedData(source_url, file, raw_text, form_name)
    db.session.add(data)
    db.session.commit()

    if request.args.get('output') == 'json':
        resp = {}
        resp['success'] = True
        resp['data'] = {
            'id': data.id,
            'original_file': data.original_file,
        }
        return jsonify(resp)

    return redirect(url_for('explore', uuid=data.id))
