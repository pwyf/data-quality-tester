from datetime import datetime, timedelta
import shutil

from flask_script import Command, Option

from IATISimpleTester.models import SuppliedData


class FlushDataCommand(Command):
    'Delete files that are older than 7 days (or all files)'

    option_list = (
        Option('--all', '-a', dest='flush_all', action='store_true'),
    )

    def run(self, flush_all=False):
        if flush_all:
            old_data = SuppliedData.query.all()
        else:
            old_data = SuppliedData.query.filter(SuppliedData.created <= datetime.utcnow() - timedelta(days=7))
        for supplied_data in old_data:
            try:
                shutil.rmtree(supplied_data.upload_dir())
            except FileNotFoundError:
                continue
