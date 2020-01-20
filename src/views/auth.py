from contextlib import contextmanager

import google.oauth2.credentials
import googleapiclient.discovery
import ldap
from aiohttp import web
from aiohttp_session import get_session
from authlib.client import OAuth2Session
from cryptography import fernet

from configmgr import config

from .base_view import BaseView


class AuthBase:
    ACCESS_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'
    AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth?access_type=offline&prompt=consent'

    AUTHORIZATION_SCOPE = 'openid email profile'

    BASE_URI = 'http://' + ':'.join(
        (config['main'].get('host'), config['main'].get('port')))
    AUTH_REDIRECT_URI = BASE_URI + '/auth'
    CLIENT_ID = config['google-auth'].get('client_id')
    CLIENT_SECRET = config['google-auth'].get('client_secret')

    AUTH_TOKEN_KEY = 'auth_token'
    AUTH_STATE_KEY = 'auth_state'


class AuthView(BaseView, AuthBase):

    @classmethod
    async def login(cls, request):
        auth_session = OAuth2Session(cls.CLIENT_ID, cls.CLIENT_SECRET,
                                     scope=cls.AUTHORIZATION_SCOPE,
                                     redirect_uri=cls.AUTH_REDIRECT_URI)

        uri, state = auth_session.create_authorization_url(cls.AUTHORIZATION_URL)

        session = await get_session(request)
        session[cls.AUTH_STATE_KEY] = state

        raise web.HTTPFound(uri)

    @classmethod
    async def google_auth_redirect(cls, request):
        req_state = request.query.get('state', None)

        session = await get_session(request)
        if req_state != session[cls.AUTH_STATE_KEY]:
            # session.pop(cls.AUTH_TOKEN_KEY, None)
            # session.pop(cls.AUTH_STATE_KEY, None)
            raise web.HTTPUnauthorized()

        auth_session = OAuth2Session(cls.CLIENT_ID, cls.CLIENT_SECRET,
                                     scope=cls.AUTHORIZATION_SCOPE,
                                     state=session[cls.AUTH_STATE_KEY],
                                     redirect_uri=cls.AUTH_REDIRECT_URI)

        oauth2_tokens = auth_session.fetch_access_token(
            cls.ACCESS_TOKEN_URI, authorization_response=str(request.url))

        session[cls.AUTH_TOKEN_KEY] = oauth2_tokens

        raise web.HTTPFound(cls.BASE_URI)

    @classmethod
    async def logout(cls, request):
        session = await get_session(request)
        session.pop(cls.AUTH_TOKEN_KEY, None)
        session.pop(cls.AUTH_STATE_KEY, None)

        raise web.HTTPFound(cls.BASE_URI)


class LDAPClient:

    def __init__(self, host=None, port=None, base_dn=None, dn_template=None):
        self.host = host or config['ldap']['host']
        self.port = port or config['ldap']['port']
        self.base_dn = base_dn or config['ldap']['base_dn']
        self.dn_template = dn_template or config['ldap']['base_dn']
        self.connection = None

    def __enter__(self):
        self.connection = ldap.initialize(f'ldap://{self.host}:{self.port}')
        self.connection.protocol_version = ldap.VERSION3
        self.connection.set_option(ldap.OPT_REFERRALS, 0)
        self.connection.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
        self.connection.set_option(ldap.OPT_X_TLS_DEMAND, True)
        self.connection.start_tls_s()
        self.connection.simple_bind_s(
            f'uid={config["ldap"]["user"]},ou=people,{config["ldap"]["base_dn"]}',
            config['ldap']['password'])
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.unbind_s()


class AuthMixin(AuthBase):

    @classmethod
    async def is_logged(cls, request):
        session = await get_session(request)
        return True if cls.AUTH_TOKEN_KEY in session else False

    @classmethod
    async def require_login(cls, func):

        async def wrapper(*args, **kwargs):
            is_logged = await cls.is_logged(args[1])
            if is_logged:
                return await func(*args, **kwargs)
            else:
                raise web.HTTPForbidden()

        return wrapper

    @classmethod
    def is_in_group(cls, uid, group):
        with LDAPClient() as con:
            group = con.search_s(f'ou=Groups,{config["ldap"]["base_dn"]}',
                                 ldap.SCOPE_SUBTREE, f'cn={group}')
            print(group)
            for member in group[0][1]['member']:
                if uid.encode() in member:
                    return True
            else:
                return False

    @classmethod
    async def require_group(cls, func):

        async def wrapper(*args, **kwargs):
            is_in_group = await cls.is_logged(args[1])
            if is_logged:
                return await func(*args, **kwargs)
            else:
                raise web.HTTPForbidden()

        return wrapper

    @classmethod
    async def build_credentials(cls, request):
        if not await cls.is_logged(request):
            raise Exception('User must be logged in')

        session = await get_session(request)
        oauth2_tokens = session[cls.AUTH_TOKEN_KEY]

        return google.oauth2.credentials.Credentials(
            oauth2_tokens['access_token'], refresh_token=oauth2_tokens['refresh_token'],
            client_id=cls.CLIENT_ID, client_secret=cls.CLIENT_SECRET,
            token_uri=cls.ACCESS_TOKEN_URI)

    @classmethod
    async def get_user_info(cls, request):
        credentials = await cls.build_credentials(request)

        oauth2_client = googleapiclient.discovery.build('oauth2', 'v2',
                                                        credentials=credentials)
        return oauth2_client.userinfo().get().execute()
