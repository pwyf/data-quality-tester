from os.path import join

from flask import render_template, request, jsonify
from werkzeug.exceptions import NotFound

from IATISimpleTester import app


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
