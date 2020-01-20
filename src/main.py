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

from app import app
from configmgr import config
from routes import routes

logging.basicConfig(level=logging.DEBUG)

app.add_routes(routes)
web.run_app(app, host=config['main']['host'], port=config['main']['port'])
