import os
import tempfile

import pytest

import DataQualityTester as dqt

os.putenv('FLASK_ENV', 'development')


@pytest.fixture
def client():
    # https://flask.palletsprojects.com/en/1.1.x/testing/
    db_fd, dqt.app.config['DATABASE'] = tempfile.mkstemp()
    dqt.app.config['TESTING'] = True

    with dqt.app.test_client() as client:
        with dqt.app.app_context():
            dqt.db.create_all()
        yield client

    os.close(db_fd)
    os.unlink(dqt.app.config['DATABASE'])


def test_landing_page(client):
    r = client.get('/')
    assert b"Data Quality Tester" in r.data


def test_post(client):
    r = client.get('/upload')
    assert b"Redirecting..." in r.data
