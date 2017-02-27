from flask import render_template, request, jsonify

from IATISimpleTester import app


@app.errorhandler(404)
def page_not_found(e):
    if request.path.endswith('.json'):
        return jsonify({'success': False, 'error': 'Not found (404)'}), 404
    return render_template('404.html'), 404
