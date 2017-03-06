import random
import string

from flask import abort, jsonify, render_template, request, session

from IATISimpleTester import app


@app.before_request
def csrf_protect():
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

@app.template_global('csrf_token')
def generate_csrf_token():
    if '_csrf_token' not in session:
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
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
    name = '{name} ({code})'.format(
        name=e.name,
        code=e.code
    )

    if request.path.endswith('.json'):
        return jsonify({'success': False, 'error': name}), e.code

    return render_template('error.html', name=name), e.code
