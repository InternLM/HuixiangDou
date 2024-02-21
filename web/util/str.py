import random
import string
import time
from web.constant.biz_constant import JWT_SECRET
import jwt
from web.model.hxd_token import HxdToken


def gen_random_string(length=4) -> str:
    """
    :param length: random string's length
    :return: a string with the given length, includes only A-Za-z0-9
    """
    # 字符集包含所有大写字母和数字
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def gen_jwt(feature_store_id: str, qa_name: str, expire: int) -> str:
    """
    :param feature_store_id:
    :param qa_name: 知识库名称
    :param expire: 过期时间 unix 时间戳
    :return: jwt
    """
    payload = {
        "iat": time.time(),
        "jti": feature_store_id,
        "qa_name": qa_name,
        "exp": expire
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def parse_jwt(token: str) -> HxdToken:
    hxd_token = jwt.decode(token, JWT_SECRET)
    return hxd_token
