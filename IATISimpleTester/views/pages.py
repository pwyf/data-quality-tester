from flask import render_template

from IATISimpleTester import app


@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/about')
def about():
    return render_template('about.html')
