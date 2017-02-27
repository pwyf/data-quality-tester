import random
import string

from flask import abort, request, session

from IATISimpleTester import app


@app.before_request
def csrf_protect():
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    if '_csrf_token' not in session:
        random_string = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
        session['_csrf_token'] = random_string
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token
