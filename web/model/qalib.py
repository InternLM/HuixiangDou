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
    docs: Optional[List] = None
    status: int
    suffix: Optional[str] = None
    feishu: Optional[Feishu] = None
    wechat: Optional[Wechat] = None
    webSearch: Optional[WebSearch] = None
