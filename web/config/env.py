import os

import lark_oapi as lark

from web.util.log import log

logger = log(__name__)


class HuixiangDouEnv:

    @classmethod
    def print_env(cls):
        methods = [
            method for method in cls.__dict__ if
            callable(getattr(HuixiangDouEnv, method)) and method != 'print_env'
        ]
        for method in methods:
            f = getattr(HuixiangDouEnv, method)
            value = f()
            logger.info(f'[config] {method}: {value}')

    @classmethod
    def get_cookie_secure(cls) -> bool:
        return True if os.getenv('COOKIE_SECURE') else False

    @classmethod
    def get_server_port(cls) -> str:
        return os.getenv('SERVER_PORT') if os.getenv(
            'SERVER_PORT') else '23333'

    @classmethod
    def get_jwt_secret(cls) -> str:
        return os.getenv('JWT_SECRET') if os.getenv(
            'JWT_SECRET') else 'HuixiangDou_is_awesome'

    @classmethod
    def get_redis_host(cls) -> str:
        return 'localhost' if os.getenv('REDIS_HOST') is None else os.getenv(
            'REDIS_HOST')

    @classmethod
    def get_redis_password(cls) -> str:
        return 'default_password' if os.getenv(
            'REDIS_PASSWORD') is None else os.getenv('REDIS_PASSWORD')

    @classmethod
    def get_redis_port(cls) -> int:
        return 6379 if os.getenv('REDIS_PORT') is None else os.getenv(
            'REDIS_PORT')

    @classmethod
    def get_redis_db(cls) -> int:
        return 0 if os.getenv('REDIS_DB') is None else os.getenv('REDIS_DB')

    @classmethod
    def _get_default_endpoint(cls) -> str:
        return f'http://0.0.0.0:{cls.get_server_port()}/'

    @classmethod
    def get_lark_encrypt_key(cls) -> str:
        return os.getenv('HUIXIANGDOU_LARK_ENCRYPT_KEY') if os.getenv(
            'HUIXIANGDOU_LARK_ENCRYPT_KEY') else 'thisiskey'

    @classmethod
    def get_lark_verification_token(cls) -> str:
        return os.getenv('HUIXIANGDOU_LARK_VERIFY_TOKEN') if os.getenv(
            'HUIXIANGDOU_LARK_VERIFY_TOKEN'
        ) else 'sMzyjKi9vMlEhKCZOVtBMhhl8x23z0AG'

    @classmethod
    def get_message_endpoint(cls) -> str:
        endpoint = os.getenv('HUIXIANGDOU_MESSAGE_ENDPOINT')
        if not endpoint:
            endpoint = cls._get_default_endpoint()
        if not endpoint.endswith('/'):
            endpoint += '/'
        return endpoint

    @classmethod
    def get_lark_log_level(cls) -> lark.LogLevel:
        return lark.LogLevel.DEBUG

    @classmethod
    def get_cookie_samesite(cls) -> str:
        return 'none' if HuixiangDouEnv.get_cookie_secure() else 'lax'
