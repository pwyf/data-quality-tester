from flask_script import Manager, Server

from DataQualityTester import app, db
from DataQualityTester.scripts import FlushDataCommand, RefreshCodelistsCommand


manager = Manager(app)
manager.add_command('runserver', Server(threaded=True))
manager.add_command('flush-data', FlushDataCommand)
manager.add_command('refresh-codelists', RefreshCodelistsCommand)

if __name__ == '__main__':
    manager.run()
