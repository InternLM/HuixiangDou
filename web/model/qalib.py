from pydantic import BaseModel
from typing import Optional, List


class Feishu(BaseModel):
    webhookUrl: str
    appId: str
    appSecret: str
    encryptKey: str
    verificationToken: str
    eventUrl: str


class Wechat(BaseModel):
    onMessageUrl: str


class WebSearch(BaseModel):
    token: str


class QalibInfo(BaseModel):
    featureStoreId: str
    name: str
    docs: Optional[List] = None
    status: int
    suffix: Optional[str] = None
    feishu: Optional[Feishu] = None
    wechat: Optional[Wechat] = None
    webSearch: Optional[WebSearch] = None


class QalibPositiveNegative(BaseModel):
    positives: Optional[List] = None
    negatives: Optional[List] = None


class QalibSample(QalibPositiveNegative):
    name: str
    featureStoreId: str


class QalibStatistic(BaseModel):
    qalibTotal: Optional[int] = None
    lastMonthUsed: Optional[int] = None
    wechatTotal: Optional[int] = None
    feishuTotal: Optional[int] = None
    servedTotal: Optional[int] = None
    realServedTotal: Optional[int] = None
