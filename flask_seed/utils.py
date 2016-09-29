# coding=utf-8

import traceback
from functools import wraps

from bson import json_util
from flask import request, current_app as app
import six


def dumps(data):
    return json_util.dumps(data, default=json_util.default)


def parse_params():
    params = request.args.to_dict()
    for key, value in six.iteritems(params):
        if key.endswith('_id'):
            params[key] = int(value)
    return params


def remove_dict_item(dict, key, default=None):
    value = default
    if key in dict:
        value = dict[key]
        del dict[key]
    return value


def get_bool(value):
    if value in ['0', 0, 'false', 'False', False, None]:
        return False
    else:
        return True


def LOG(type):
    def _log(func):
        @wraps(func)
        def __log(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
            except Exception:
                with app.app_context():
                    app.logger.error('{path} {type} failed. \n{reason}'.format(
                        path=request.path, type=type,
                        reason=traceback.format_exc()
                    ))
                raise
            else:
                with app.app_context():
                    app.logger.info('{path} {type} success.'.format(
                        path=request.path, type=type))
                return res

        return __log

    return _log
