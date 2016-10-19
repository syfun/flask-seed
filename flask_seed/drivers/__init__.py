# coding=utf-8

from .mongo import MongoDriver, MongoBase
from .sql import SQLDriver, SQLBase


def get_db_driver(name):
    if name == 'mongo':
        return MongoDriver(), MongoBase
    elif name == 'sql':
        return SQLDriver(), SQLBase
    else:
        raise RuntimeError('{} is not correct db driver name.'.format(name))
