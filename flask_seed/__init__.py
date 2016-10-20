# coding=utf-8

import logging
from logging.handlers import RotatingFileHandler

from gevent.wsgi import WSGIServer
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication

from .exceptions import HTTPError, handle_http_error
from .handlers import BaseHandler
from .drivers import get_db_driver


class Seed(object):

    def __init__(self, app=None, config_prefix='SEED'):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app, config_prefix='SEED'):
        self.app = app

        # Custom HTTP Error
        app.errorhandler(HTTPError)(handle_http_error)

        def key(suffix):
            return '%s_%s' % (config_prefix, suffix)

        # set database driver
        db_driver = app.config.get(key('DB_DRIVER'), None)
        if db_driver:
            try:
                db_driver, base_model = get_db_driver(db_driver)
            except RuntimeError as exc:
                raise
            else:
                globals()['BaseModel'] = base_model
                self.db_driver = db_driver(app)
        else:
            self.db_driver = None
        if not getattr(app, 'db_driver', None):
            setattr(app, 'db_driver', self.db_driver)

        # app logger add RotatingFileHandler.
        log_file = app.config.get(key('LOG_FILE'), None)
        if log_file:
            logger_handler = RotatingFileHandler(log_file)
            logger_handler.setLevel(app.config.get(key('LOG_LEVEL'), 'DEBUG'))
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s '
                '[in %(pathname)s:%(lineno)d]')
            logger_handler.setFormatter(
                app.config.get(key('LOG_FORMATTER'), formatter))
            app.logger.addHandler(logger_handler)

    def register_models(self, models=None):
        # self.app.app_context().push()
        models = models or Models
        with self.app.app_context():
            self.db_driver.register(models)

    def register_handlers(self, handlers=None, **options):
        handlers = handlers or Handlers
        with self.app.app_context():
            for h in handlers:
                self.app.register_blueprint(h().blueprint, **options)


class Set(object):

    def __init__(self):
        self.items = []

    def register(self, item):
        self.items.append(item)
        return item

    def __iter__(self):
        return iter(self.items)

Models = Set()
Handlers = Set()
