import configparser
import logging
import os

import aiohttp_jinja2
import jinja2
import motor.motor_asyncio
from aiohttp import web
from aiohttp_session import get_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from pytz import timezone

from configmgr import config
from data_puller import CustomerData

TEMPLATE_PATH = 'src/templates'

app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_PATH))
setup(app, EncryptedCookieStorage(b'Thirty  two  length  bytes  key.'))

mongo_config = config['mongo']
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_config['address'])
