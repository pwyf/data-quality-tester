from flask import render_template


def home():
    return render_template('upload.html')

def about():
    return render_template('about.html')
