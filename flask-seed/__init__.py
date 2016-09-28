# coding=utf-8

from .mongo import MongoDB


class Seed(object):

    def __init__(self, app=None):
        self.app = app
        self.mongo = MongoDB(app)
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.mongo.init_app(app)
