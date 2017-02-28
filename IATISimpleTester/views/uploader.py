import os.path

from flask import abort, flash, request, jsonify, redirect, url_for

from IATISimpleTester import app, db
from IATISimpleTester.models import SuppliedData


@app.route('/upload.json', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    api_request = request.path.endswith('json')
    if request.method == 'POST':
        form_data = request.form
    else:
        form_data = request.args
    source_url = form_data.get('source_url')
    original_file = request.files.get('original_file')
    raw_text = form_data.get('paste')
    form_name = None

    if source_url:
        form_name = 'url_form'
    elif raw_text:
        form_name = 'text_form'
    elif original_file:
        form_name = 'upload_form'

    if not form_name:
        # no form data submitted.
        # Do something sensible here
        if api_request:
            return abort(404)
        flash('Something went wrong.', 'danger')
        return redirect(url_for('home'))

    data = SuppliedData(source_url, original_file, raw_text, form_name)
    db.session.add(data)
    db.session.commit()

    if api_request:
        resp = {}
        resp['success'] = True
        resp['data'] = {
            'id': data.id,
            'original_file': data.original_file,
        }
        return jsonify(resp)

    return redirect(url_for('explore', uuid=data.id))
