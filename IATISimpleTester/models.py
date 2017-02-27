from datetime import datetime
from enum import Enum
from os import makedirs
from os.path import join, dirname
from urllib.parse import urlparse
import uuid

import requests
import rfc6266  # (content-disposition header parser)
from werkzeug.utils import secure_filename

from IATISimpleTester import app, db


class BadUrlException(Exception):
    pass


class SuppliedData(db.Model):
    class FormName(Enum):
        upload_form = 'File upload'
        url_form = 'Downloaded from URL'
        text_form = 'Pasted into textarea'


    id = db.Column(db.String(40), primary_key=True)
    source_url = db.Column(db.String(2000))
    original_file = db.Column(db.String(100))
    form_name = db.Column(db.Enum(FormName))
    created = db.Column(db.DateTime)

    def allowed_file_extension(self, filename):
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def generate_uuid(self):
       return str(uuid.uuid4())

    def is_valid(self, url):
        qualifying = ('scheme', 'netloc',)
        token = urlparse(url)
        return all([getattr(token, qualifying_attr)
            for qualifying_attr in qualifying])

    def upload_dir(self):
        return join(app.config['MEDIA_FOLDER'], self.id)

    def path_to_file(self):
        return join(app.config['MEDIA_FOLDER'], self.original_file)

    def download(self, url):
        if not self.is_valid(url):
            raise BadUrlException
        r = requests.get(url, headers={'User-Agent': 'Publish What You Fund Simple Tester'}, stream=True)
        r.raise_for_status()
        content_type = r.headers.get('content-type', '').split(';')[0].lower()
        file_extension = None
        if content_type in ('text/xml', 'application/xml',):
            file_extension = 'xml'

        if not file_extension:
            possible_extension = rfc6266.parse_requests_response(r).filename_unsafe.split('.')[-1]
            if possible_extension == 'xml':
                file_extension = possible_extension

        filename = r.url.split('/')[-1].split('?')[0][:100]
        if filename == '':
            filename = 'file'
        if file_extension:
            if not filename.endswith(file_extension):
                filename = filename + '.' + file_extension
        filename = secure_filename(filename)
        makedirs(self.upload_dir(), exist_ok=True)
        filepath = join(self.upload_dir(), filename)
        with open(filepath, 'wb') as f:
            for block in r.iter_content(1024):
                f.write(block)
        return filename

    def __init__(self, source_url, file, raw_text, form_name):
        self.id = self.generate_uuid()

        if source_url:
            filename = self.download(source_url)
        elif file:
            if file.filename != '' and self.allowed_file_extension(file.filename):
                # save the file
                filename = file.filename
                filename = secure_filename(filename)
                makedirs(self.upload_dir(), exist_ok=True)
                filepath = join(self.upload_dir(), filename)
                file.save(filepath)
        elif raw_text:
            filename = 'test.xml'
            makedirs(self.upload_dir(), exist_ok=True)
            filepath = join(self.upload_dir(), filename)
            with open(filepath, 'w') as f:
                f.write(raw_text)

        self.source_url = source_url
        self.original_file = join(self.id, filename)
        self.form_name = form_name

        self.created = datetime.utcnow()
