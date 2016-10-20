# coding=utf-8

from flask import current_app as app


def db(operation):
    with app.app_context():
        if operation == 'init':
            app.db_driver.init_db()
        elif operation == 'migrate':
            app.db_driver.migrate()
        elif operation == 'drop':
            app.db_driver.drop_db()
