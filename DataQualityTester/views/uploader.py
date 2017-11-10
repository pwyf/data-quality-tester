from flask import flash, jsonify, redirect, request, url_for
from werkzeug.datastructures import FileStorage

from DataQualityTester import db
from DataQualityTester.lib.exceptions import BadUrlException, \
    NoFormDataException
from DataQualityTester.models import SuppliedData


def upload():
    try:
        supplied_data = _upload()
    except (NoFormDataException, BadUrlException) as e:
        flash(str(e), 'danger')
        return redirect(url_for('home'))

    next_url = url_for('package_overview', uuid=supplied_data.id)

    if request.is_xhr:
        task_url = url_for('task_status', task_id=supplied_data.task_id)
        return jsonify({'task_url': task_url, 'next_url': next_url})

    return redirect(next_url)


def load_sample():
    filename = 'sample.xml'
    with open(filename, 'rb') as fh:
        original_file = FileStorage(fh)
        supplied_data = SuppliedData(None, original_file, None, 'upload_form')
    db.session.add(supplied_data)
    db.session.commit()
    return redirect(url_for('package_overview', uuid=supplied_data.id))


def _upload():
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
        raise NoFormDataException(
            'The form didn\'t submit properly. Please try again.')

    supplied_data = SuppliedData(source_url, original_file,
                                 raw_text, form_name)
    db.session.add(supplied_data)
    db.session.commit()

    return supplied_data
