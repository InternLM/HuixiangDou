import os
import random
import string
import time
from typing import List

import jwt
from fastapi import HTTPException

from web.config.env import HuixiangDouEnv


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
        'iat': time.time(),
        'jti': feature_store_id,
        'qa_name': qa_name,
        'exp': expire
    }
    token = jwt.encode(payload,
                       HuixiangDouEnv.get_jwt_secret(),
                       algorithm='HS256')
    return token


def parse_jwt(token: str) -> dict:
    hxd_token = jwt.decode(token,
                           HuixiangDouEnv.get_jwt_secret(),
                           algorithms='HS256')
    return hxd_token


def safe_join(directory: str, path: str) -> str:
    """Safely path to a base directory to avoid escaping the base directory.
    Borrowed from: werkzeug.security.safe_join.

    @param directory:
    @param path:
    """
    _os_alt_seps: List[str] = [
        sep for sep in [os.path.sep, os.path.altsep]
        if sep is not None and sep != '/'
    ]

    if path == '':
        raise HTTPException(status_code=400, detail='path is empty')

    filename = os.path.normpath(path)
    full_path = os.path.join(directory, filename)
    if (any(sep in filename for sep in _os_alt_seps) or os.path.isabs(filename)
            or filename == '..' or filename.startswith('../')
            or os.path.isdir(full_path)):
        raise HTTPException(status_code=400, detail='path is illegal')

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail='path is not existed')
    return full_path
