from flask import flash, redirect, request, url_for

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
