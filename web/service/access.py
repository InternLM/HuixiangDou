import time

from web.model.access import LoginBody
from web.model.base import BaseBody
from web.orm.redis import r
from web.util.log import log
from passlib.hash import bcrypt
import web.constant.biz_constant as biz_const
import web.util.str as str
from fastapi import Response

logger = log(__name__)


def _create_qa_lib(name, hashed_pass, feature_store_id) -> bool:
    if 1 != r.hsetnx(name=biz_const.RDS_KEY_LOGIN, key=name, value=f"{hashed_pass}||{feature_store_id}"):
        return False
    return True


class LoginService:
    def __init__(self, login: LoginBody, response: Response):
        self.name = login.name
        self.password = login.password
        self.response = response

    async def login(self):
        # calc the password hashcode
        login_info = r.hget(name=biz_const.RDS_KEY_LOGIN, key=self.name)

        gen_hashed_pass = bcrypt.hash(self.password)
        # qalib not existed, create one
        if not login_info:
            feature_store_id = str.gen_random_string()
            if not _create_qa_lib(self.name, gen_hashed_pass, feature_store_id):
                self.response.delete_cookie(key=biz_const.HXD_COOKIE_KEY)
                return BaseBody(
                    msg=biz_const.ERR_ACCESS_CREATE.get("msg"),
                    msgCode=biz_const.ERR_ACCESS_CREATE.get("code")
                )
            # todo domain need to set
            self.response.set_cookie(
                key=biz_const.HXD_COOKIE_KEY,
                value=str.gen_jwt(feature_store_id, self.name, int(round(time.time() * 1000) + 604800000)),
                max_age=604800,
                expires=604800,
            )
            return BaseBody(
                data={
                    "exist": False,
                    "featureStoreId": feature_store_id
                }
            )
        # qalib existed
        else:
            login_info = bytes.decode(login_info)
            saved_hashed_pass = login_info.split("||")[0]
            # auth succeed
            if bcrypt.verify(self.password, saved_hashed_pass):
                feature_store_id = login_info.split("||")[1]
            # auth failed
            else:
                return BaseBody(
                    msg=biz_const.ERR_ACCESS_LOGIN.get("msg"),
                    msgCode=biz_const.ERR_ACCESS_LOGIN.get("code")
                )
        # todo domain need to set
        self.response.set_cookie(
            key=biz_const.HXD_COOKIE_KEY,
            value=str.gen_jwt(feature_store_id, self.name, int(round(time.time() * 1000) + 604800000)),
            max_age=604800,
            expires=604800,
        )
        return BaseBody(
            data={
                "exist": True,
                "featureStoreId": feature_store_id
            }
        )
