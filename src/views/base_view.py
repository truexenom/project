import datetime
import functools
import json

from app import config, mongo_client


def serializer(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f'Object {obj} of type {type(obj)} is not serializable')


class BaseView:
    yesterday = datetime.datetime.today() - datetime.timedelta(days=2)
    mongo_client = mongo_client
    config = config
    dumper = functools.partial(json.dumps, default=serializer)
