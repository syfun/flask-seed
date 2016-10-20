# coding=utf-8

from flask_sqlalchemy import SQLAlchemy


class SQLDriver(SQLAlchemy):
    """SQLDRIVER"""

    def init_db():
        self.create_all()

    def drop_db():
        self.drop_all()


class SQLBase(object):
    pass
