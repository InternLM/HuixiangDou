import time

from web.model.base import BaseBody
from web.orm.redis import r
from web.util.log import log
import web.util.str as str_util
import web.constant.biz_constant as biz_const
from fastapi import Response, Request
from web.model.hxd_token import HxdToken


logger = log(__name__)


class QaLibService:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    async def info(self) -> BaseBody:
        cookies = self.request.cookies
        if not cookies or not cookies.get(biz_const.HXD_COOKIE_KEY):
            return BaseBody(
                msg=biz_const.ERR_QALIB_API_NO_ACCESS.get("msg"),
                msgCode=biz_const.ERR_QALIB_API_NO_ACCESS.get("code")
            )
        hxd_token = str_util.parse_jwt(cookies.get(biz_const.HXD_COOKIE_KEY))
        feature_store_id = hxd_token.jti
        o = r.hget(biz_const.RDS_KEY_QALIB_INFO, feature_store_id)
        if not o:
            return BaseBody(
                msg=biz_const.ERR_QALIB_INFO_NOT_FOUND.get("msg"),
                msgCode=biz_const.ERR_QALIB_INFO_NOT_FOUND.get("code")
            )
        # todo
        return BaseBody(
            data={
                "exist": True,
                "featureStoreId": None
            }
        )
