from fastapi import Request, Response

import web.constant.biz_constant as biz_const
from web.model.base import BaseBody
from web.model.chat import ChatType
from web.model.statistic import StatisticTotal
from web.orm.redis import r
from web.service.cache import ChatCache
from web.util.log import log

logger = log(__name__)


class StatisticService:

    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    async def info_statistic(self):
        qalib_total = r.hlen(biz_const.RDS_KEY_QALIB_INFO)
        monthly_active = ChatCache.get_monthly_active()
        lark_used = ChatCache.hlen_agent_used(ChatType.LARK)
        wechat_used = ChatCache.hlen_agent_used(ChatType.WECHAT)
        total_inference = ChatCache.get_inference_number()
        unique_user = ChatCache.get_unique_inference_user_number()

        data = StatisticTotal(qalibTotal=qalib_total,
                              lastMonthUsed=monthly_active,
                              wechatTotal=wechat_used,
                              feishuTotal=lark_used,
                              servedTotal=total_inference,
                              realServedTotal=unique_user)
        return BaseBody(data=data)
