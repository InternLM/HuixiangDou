from typing import Optional

from pydantic import BaseModel


class StatisticTotal(BaseModel):
    qalibTotal: Optional[int] = None
    lastMonthUsed: Optional[int] = None
    wechatTotal: Optional[int] = None
    feishuTotal: Optional[int] = None
    servedTotal: Optional[int] = None
    realServedTotal: Optional[int] = None
