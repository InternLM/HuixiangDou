from web.model.base import BaseBody
from web.model.statistic import StatisticTotal
from web.orm.redis import r
from web.util.log import log
import web.constant.biz_constant as biz_const
from fastapi import Response, Request

logger = log(__name__)


class StatisticService:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    async def info_statistic(self):
        qalib_total = r.hlen(biz_const.RDS_KEY_QALIB_INFO)
        # todo more statistic data will be added
        data = StatisticTotal(qalibTotal=qalib_total)
        return BaseBody(
            data=data
        )
