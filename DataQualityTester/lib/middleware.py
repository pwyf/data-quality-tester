import random
import string

from flask import abort, jsonify, render_template, request, session

from DataQualityTester import app


@app.before_request
def csrf_protect():
    if request.method == 'POST':
        token = session.get('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


@app.template_global('csrf_token')
def generate_csrf_token():
    if '_csrf_token' not in session:
        random_string = ''.join(
            [random.choice(string.ascii_letters + string.digits)
             for n in range(32)])
        session['_csrf_token'] = random_string
    return session['_csrf_token']


@app.errorhandler(404)
def not_found(e):
    return generic_error(e)


@app.errorhandler(403)
def access_denied(e):
    return generic_error(e)


@app.errorhandler(500)
def server_error(e):
    return generic_error(e)


def generic_error(e):
    try:
        err_code = e.code
        error_str = '{name} ({code})'.format(
            name=e.name,
            code=err_code
        )
    except Exception:
        error_str = 'Unknown error'
        err_code = 500

    if request.path.endswith('.json'):
        return jsonify({'success': False, 'error': error_str}), err_code

    return render_template('error.html', name=error_str), err_code
