import json
import time

from fastapi import Request, Response
from passlib.hash import bcrypt

import web.constant.biz_constant as biz_const
import web.util.str as str
from web.config.env import HuixiangDouEnv
from web.model.access import AccessInfo, LoginBody
from web.model.base import BaseBody
from web.orm.redis import r
from web.service.qalib import QaLibCache, gen_suffix
from web.util.log import log

logger = log(__name__)


def add_access_info(name, value) -> bool:
    """add new access info to access:info db.

    :param name:
    :param value:
    :return:
    """
    return False if 1 != r.hset(
        name=biz_const.RDS_KEY_LOGIN, key=name, value=value) else True


def del_access_info(name) -> bool:
    """del new access info from access:info db.

    :param name:
    :return:
    """
    return True if 1 == r.hdel(biz_const.RDS_KEY_LOGIN, name) else False


def _create_qa_lib(name, hashed_pass, feature_store_id) -> bool:
    """
    1. init access info
    2. init qalib info
    :param name:
    :param hashed_pass:
    :param feature_store_id:
    :return:
    """
    try:
        if not add_access_info(
                name,
                AccessInfo(hashpass=hashed_pass,
                           featureStoreId=feature_store_id).model_dump_json()):
            return False
        suffix = gen_suffix(feature_store_id)
        if not QaLibCache().init_qalib_info(
                feature_store_id, biz_const.HXD_QALIB_STATUS_INIT, name,
                suffix):
            if not del_access_info(name):
                logger.error(f'del access info by {name} failed')
            return False

        # store suffix -> feature_store_id
        QaLibCache().set_suffix_to_qalib(suffix, feature_store_id)
        return True
    except Exception as e:
        logger.error(f'[create] create name: {name} failed: {e}')
        if not del_access_info(name):
            logger.error(f'del access info by {name} failed')
        if not QaLibCache().del_qalib_info(feature_store_id):
            logger.error(f'del qalib info by {name} failed')
        return False


class LoginService:

    def __init__(self, login: LoginBody, request: Request, response: Response):
        self.name = login.name
        self.password = login.password
        self.response = response
        self.request = request

    def _set_cookie(self, cookie_key, *jwt_payloads):
        self.response.set_cookie(
            key=cookie_key,
            value=str.gen_jwt(jwt_payloads[0][0], jwt_payloads[0][1],
                              int(round(time.time() * 1000) + 604800000)),
            max_age=604800,
            expires=604800,
            # only send cookie in https when secure is True
            secure=HuixiangDouEnv.get_cookie_secure(),
            # cookie will be sent in all requests, including cross-site's requests
            # to make sure the huixiangdou's cookie can be transformed in OpenXLab-Apps
            samesite=HuixiangDouEnv.get_cookie_samesite())

    async def login(self):
        if not self.name or len(self.name) < 8:
            logger.error(f'login name={self.name} not valid.')
            return BaseBody(msg=biz_const.ERR_ACCESS_LOGIN.get('msg'),
                            msgCode=biz_const.ERR_ACCESS_LOGIN.get('code'))

        # calc the password hashcode
        o = r.hget(name=biz_const.RDS_KEY_LOGIN, key=self.name)

        gen_hashed_pass = bcrypt.hash(self.password)
        # qalib not existed, create one
        if not o:
            feature_store_id = str.gen_random_string()
            # create qalib
            if not _create_qa_lib(self.name, gen_hashed_pass,
                                  feature_store_id):
                self.response.delete_cookie(key=biz_const.HXD_COOKIE_KEY)
                return BaseBody(
                    msg=biz_const.ERR_ACCESS_CREATE.get('msg'),
                    msgCode=biz_const.ERR_ACCESS_CREATE.get('code'))

            # set cookies
            # todo domain need to set？
            self._set_cookie(biz_const.HXD_COOKIE_KEY,
                             [feature_store_id, self.name])
            return BaseBody(data={
                'exist': False,
                'featureStoreId': feature_store_id
            })
        # qalib existed
        else:
            access_info = AccessInfo(**json.loads(bytes.decode(o)))
            # auth succeed
            if bcrypt.verify(self.password, access_info.hashpass):
                feature_store_id = access_info.featureStoreId
            # auth failed
            else:
                return BaseBody(msg=biz_const.ERR_ACCESS_LOGIN.get('msg'),
                                msgCode=biz_const.ERR_ACCESS_LOGIN.get('code'))
        # todo domain need to set
        self._set_cookie(biz_const.HXD_COOKIE_KEY,
                         [feature_store_id, self.name])
        return BaseBody(data={
            'exist': True,
            'featureStoreId': feature_store_id
        })
