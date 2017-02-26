from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from IATISimpleTester import app, db
from IATISimpleTester.scripts import FlushDataCommand


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('flush-data', FlushDataCommand)

if __name__ == '__main__':
    manager.run()
