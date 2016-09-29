# coding=utf-8

import logging
from logging.handlers import RotatingFileHandler

from gevent.wsgi import WSGIServer
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication

from .mongo import MongoDB, BaseModel
from .exceptions import HTTPError, handle_http_error
from .handler import BaseHandler


class Seed(object):

    def __init__(self, app=None, config_prefix='SEED'):
        self.app = app
        self.mongo = MongoDB(app, config_prefix)
        if app is not None:
            self.init_app(app)

    def init_app(self, app, config_prefix='SEED'):
        self.mongo.init_app(app)
        if not getattr(app, 'mongo'):
            setattr(app, 'mongo', self.mongo)

        # Custom HTTP Error
        app.errorhandler(HTTPError)(handle_http_error)

        def key(suffix):
            return '%s_%s' % (config_prefix, suffix)

        # app logger add RotatingFileHandler.
        logger_handler = RotatingFileHandler(
            app.config.get(key('LOG_FILE'), 'flask.log'))
        logger_handler.setLevel(app.config.get(key('LOG_LEVEL'), 'INFO'))
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s '
            '[in %(pathname)s:%(lineno)d]')
        logger_handler.setFormatter(
            app.config.get(key('LOG_FORMATTER'), formatter))
        app.logger.addHandler(logger_handler)

    def register_models(self, models):
        # self.app.app_context().push()
        with self.app.app_context():
            self.mongo.register(models)

    def register_handlers(self, handlers, **options):
        with self.app.app_context():
            for h in handlers:
                self.app.register_blueprint(h().blueprint, **options)

    def runserver(self, host='127.0.0.1', port=5000):
        @run_with_reloader
        def run():
            if self.app.debug:
                self.app = DebuggedApplication(self.app)
            http_server = WSGIServer(
                (host, port),
                self.app
            )
            http_server.serve_forever()
        return run


class ModelSet(object):
    def __init__(self):
        self.models = []

    def add(self, model):
        self.models.append(model)
        return model


class HandlerSet(object):
    def __init__(self):
        self.handlers = []

    def add(self, handler):
        self.handlers.append(handler)
        return handler

model_set = ModelSet()
handler_set = HandlerSet()
