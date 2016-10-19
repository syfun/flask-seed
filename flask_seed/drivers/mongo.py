# coding=utf-8

from time import strftime

import pymongo
import pymongo.errors
from pymongo import ReturnDocument, uri_parser
from pymongo.read_preferences import ReadPreference
from flask_pymongo import PyMongo, BSONObjectIdConverter
from flask_pymongo.wrappers import MongoClient, MongoReplicaSetClient
from flask import current_app

import six

DAY_FORMAT = '%Y%m%d'


class MongoDriver(PyMongo):

    def __init__(self, app=None, config_prefix='MONGO'):
        super(MongoDriver, self).__init__(app, config_prefix)
        self.col_classes = []

    def init_app(self, app, config_prefix='MONGO'):
        """Initialize the `app` for use with this :class:`~PyMongo`. This is
        called automatically if `app` is passed to :meth:`~PyMongo.__init__`.
        The app is configured according to the configuration variables
        ``PREFIX_HOST``, ``PREFIX_PORT``, ``PREFIX_DBNAME``,
        ``PREFIX_AUTO_START_REQUEST``,
        ``PREFIX_REPLICA_SET``, ``PREFIX_READ_PREFERENCE``,
        ``PREFIX_USERNAME``, ``PREFIX_PASSWORD``, and ``PREFIX_URI`` where
        "PREFIX" defaults to "MONGO". If ``PREFIX_URL`` is set, it is
        assumed to have all appropriate configurations, and the other
        keys are overwritten using their values as present in the URI.
        :param flask.Flask app: the application to configure for use with
           this :class:`~PyMongo`
        :param str config_prefix: determines the set of configuration
           variables used to configure this :class:`~PyMongo`
        """
        if 'pymongo' not in app.extensions:
            app.extensions['pymongo'] = {}

        if config_prefix in app.extensions['pymongo']:
            raise Exception('duplicate config_prefix "%s"' % config_prefix)

        self.config_prefix = config_prefix

        def key(suffix):
            return '%s_%s' % (config_prefix, suffix)

        if key('URI') in app.config:
            # bootstrap configuration from the URL
            parsed = uri_parser.parse_uri(app.config[key('URI')])
            if not parsed.get('database'):
                raise ValueError('MongoDB URI does not contain database name')
            app.config[key('DBNAME')] = parsed['database']
            app.config[key('READ_PREFERENCE')] = parsed['options'].get(
                'read_preference')
            app.config[key('USERNAME')] = parsed['username']
            app.config[key('PASSWORD')] = parsed['password']
            app.config[key('REPLICA_SET')] = parsed['options'].get(
                'replica_set')
            app.config[key('MAX_POOL_SIZE')] = parsed['options'].get(
                'max_pool_size')
            app.config[key('SOCKET_TIMEOUT_MS')] = parsed['options'].get(
                'socket_timeout_ms', None)
            app.config[key('CONNECT_TIMEOUT_MS')] = parsed['options'].get(
                'connect_timeout_ms', None)
            app.config[key('AUTH_MECHANISM')] = parsed['options'].get(
                'authmechanism', 'DEFAULT')

            if pymongo.version_tuple[0] < 3:
                app.config[key('AUTO_START_REQUEST')] = parsed['options'].get(
                    'auto_start_request', True)
            else:
                app.config[key('CONNECT')] = parsed['options'].get('connect',
                                                                   True)

            # we will use the URI for connecting instead of HOST/PORT
            app.config.pop(key('HOST'), None)
            app.config.setdefault(key('PORT'), 27017)
            host = app.config[key('URI')]

        else:
            app.config.setdefault(key('HOST'), 'localhost')
            app.config.setdefault(key('PORT'), 27017)
            app.config.setdefault(key('DBNAME'), app.name)
            app.config.setdefault(key('READ_PREFERENCE'), None)
            app.config.setdefault(key('SOCKET_TIMEOUT_MS'), None)
            app.config.setdefault(key('CONNECT_TIMEOUT_MS'), None)
            app.config.setdefault(key('AUTH_MECHANISM'), 'DEFAULT')

            if pymongo.version_tuple[0] < 3:
                app.config.setdefault(key('AUTO_START_REQUEST'), True)
            else:
                app.config.setdefault(key('CONNECT'), True)

            # these don't have defaults
            app.config.setdefault(key('USERNAME'), None)
            app.config.setdefault(key('PASSWORD'), None)
            app.config.setdefault(key('REPLICA_SET'), None)
            app.config.setdefault(key('MAX_POOL_SIZE'), None)

            try:
                int(app.config[key('PORT')])
            except ValueError:
                raise TypeError('%s_PORT must be an integer' % config_prefix)

            host = app.config[key('HOST')]

        username = app.config[key('USERNAME')]
        password = app.config[key('PASSWORD')]

        auth = (username, password)

        if any(auth) and not all(auth):
            raise Exception('Must set both USERNAME and PASSWORD or neither')

        read_preference = app.config[key('READ_PREFERENCE')]
        if isinstance(read_preference, six.text_type):
            # Assume the string to be the name of the read
            # preference, and look it up from PyMongo
            read_preference = getattr(ReadPreference, read_preference)
            if read_preference is None:
                raise ValueError(
                    '%s_READ_PREFERENCE: No such read preference name (%r)' %
                    (config_prefix, read_preference))
            app.config[key('READ_PREFERENCE')] = read_preference
        # Else assume read_preference is already a valid constant
        # from pymongo.read_preferences.ReadPreference or None

        replica_set = app.config[key('REPLICA_SET')]
        dbname = app.config[key('DBNAME')]
        max_pool_size = app.config[key('MAX_POOL_SIZE')]
        socket_timeout_ms = app.config[key('SOCKET_TIMEOUT_MS')]
        connect_timeout_ms = app.config[key('CONNECT_TIMEOUT_MS')]

        if pymongo.version_tuple[0] < 3:
            auto_start_request = app.config[key('AUTO_START_REQUEST')]
            if auto_start_request not in (True, False):
                raise TypeError('%s_AUTO_START_REQUEST must be a bool' %
                                config_prefix)

        # document class is not supported by URI, using setdefault in all cases
        document_class = app.config.setdefault(key('DOCUMENT_CLASS'), None)

        args = [host]

        kwargs = {
            'port': int(app.config[key('PORT')]),
            'tz_aware': True,
        }
        if pymongo.version_tuple[0] < 3:
            kwargs['auto_start_request'] = auto_start_request
        else:
            kwargs['connect'] = app.config[key('CONNECT')]

        if read_preference is not None:
            kwargs['read_preference'] = read_preference

        if socket_timeout_ms is not None:
            kwargs['socketTimeoutMS'] = socket_timeout_ms

        if connect_timeout_ms is not None:
            kwargs['connectTimeoutMS'] = connect_timeout_ms

        if pymongo.version_tuple[0] < 3:
            if replica_set is not None:
                kwargs['replicaSet'] = replica_set
                connection_cls = MongoReplicaSetClient
            else:
                connection_cls = MongoClient
        else:
            kwargs['replicaSet'] = replica_set
            connection_cls = MongoClient

        if max_pool_size is not None:
            kwargs['max_pool_size'] = max_pool_size

        if document_class is not None:
            kwargs['document_class'] = document_class

        cx = connection_cls(*args, **kwargs)
        db = cx[dbname]

        if any(auth):
            mechanism = app.config[key('AUTH_MECHANISM')]
            db.authenticate(username, password, mechanism=mechanism)

        app.extensions['pymongo'][config_prefix] = (cx, db)
        app.url_map.converters['ObjectId'] = BSONObjectIdConverter

    def init_db(self):
        self.init_indexes()
        self.init_ids()

    def init_indexes(self):
        try:
            for cls in self.col_classes:
                col = self.db[cls.__collection__]
                index = cls.indexes
                if not index:
                    continue
                if 'expireAfterSeconds' in index:
                    col.create_index(index['name'], expireAfterSeconds=index[
                        'expireAfterSeconds'])
                if 'unique' in index:
                    col.create_index(index['name'], unique=index['unique'])
        except pymongo.errors.CollectionInvalid:
            pass

    def init_ids(self):
        for cls in self.col_classes:
            res = self.db.ids.find_one(dict(name=cls.__collection__))
            if not res:
                self.db.ids.insert_one(
                    dict(name=cls.__collection__, id=0))
        res = self.db.ids.find_one(dict(name='todo_serial_number'))
        if not res:
            today = strftime(DAY_FORMAT)
            self.db.ids.insert_one(
                dict(name='todo_serial_number', id=0, today=today)
            )

    def register(self, models):
        for model in models:
            self.col_classes.append(model)
            setattr(self, model.__name__, model())

    def get_id(self, collection):
        res = self.db.ids.find_one_and_update(
            dict(name=collection),
            {'$inc': {'id': 1}},
            return_document=ReturnDocument.AFTER
        )
        return res['id']

    def get_serial_number(self):
        filter = dict(name='todo_serial_number')
        todo_serial_number = self.db.ids.find_one(filter)
        today = strftime(DAY_FORMAT)
        if today == todo_serial_number['today']:
            res = self.db.ids.find_one_and_update(
                filter,
                {'$inc': {'id': 1}},
                return_document=ReturnDocument.AFTER
            )
            id = int(res['id'])
            if id > 9999:
                return '{today}{id}'.format(today=today, id=id)
            else:
                return '{today}{id:0>4}'.format(today=today, id=id)

        else:
            self.db.ids.find_one_and_update(
                filter,
                {'$set': {'id': 1, 'today': today}}
            )
            return today + '0001'


class MongoBase(object):
    """Base class for mongodb collection.

    In subclass need define _collection and _required_keys.
    _collection is collection that you want to use.
    _required_keys is a tuple-in list containing all required keys,
    first tuple value is key, second is none value of key type.

    Example:
        class Customer(Base):

            __collection__ = 'customers'
            required_fields = [('name', ''), ('number', 0)]
            dbref = {
                'user_id': 'User'
            }
    """

    __collection__ = ''
    indexes = {}
    required_fields = []
    dbref = {}

    def __init__(self):
        self.collection = current_app.db_driver.db[self.__collection__]

    def query(self, filter=None, sort=None, projection=None,
              skip=0, limit=0, **kwargs):
        cursor = self.collection.find(
            filter=filter, projection=projection,
            skip=skip, limit=limit, **kwargs)
        if sort:
            cursor.sort(sort)
        return cursor

    def get(self, doc_id, projection=None):
        try:
            doc_id = int(doc_id)
        finally:
            doc = self.collection.find_one(
                {'_id': doc_id}, projection=projection
            )
            return doc

    def create(self, new_doc):
        new_doc['_id'] = current_app.db_driver.get_id(self.__collection__)
        self.collection.insert_one(new_doc)
        return new_doc

    def update(self, doc_id, new_doc, unset=None, projection=None):
        try:
            doc_id = int(doc_id)
        finally:
            if unset is not None:
                res = self.collection.find_one_and_update(
                    {'_id': doc_id}, {'$set': new_doc, '$unset': unset},
                    return_document=ReturnDocument.AFTER,
                    projection=projection
                )
            else:
                res = self.collection.find_one_and_update(
                    {'_id': doc_id}, {'$set': new_doc},
                    return_document=ReturnDocument.AFTER,
                    projection=projection
                )
            return res

    def delete(self, doc_id):
        try:
            doc_id = int(doc_id)
        finally:
            res = self.collection.delete_one({'_id': doc_id})
            if res.deleted_count == 1:
                return True
            else:
                return False

    def __getattr__(self, name):
        attr = getattr(self.collection, name)
        if not attr:
            raise AttributeError()
        else:
            return attr
