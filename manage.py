from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand

from IATISimpleTester import app, db
from IATISimpleTester.scripts import FlushDataCommand, RefreshCodelistsCommand


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('runserver', Server(threaded=True))
manager.add_command('db', MigrateCommand)
manager.add_command('flush-data', FlushDataCommand)
manager.add_command('refresh-codelists', RefreshCodelistsCommand)

if __name__ == '__main__':
    manager.run()
