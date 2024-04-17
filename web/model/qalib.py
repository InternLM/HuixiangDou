from typing import List, Optional

from pydantic import BaseModel


class Lark(BaseModel):
    appId: Optional[str] = ''
    appSecret: Optional[str] = ''
    encryptKey: str
    verificationToken: str
    eventUrl: str


class Wechat(BaseModel):
    onMessageUrl: str


class WebSearch(BaseModel):
    token: str


class FilesState(BaseModel):
    file: str
    status: bool
    desc: str


class QalibInfo(BaseModel):
    featureStoreId: Optional[str] = None
    name: Optional[str] = None
    docs: Optional[List[str]] = []
    docBase: Optional[str] = None
    status: Optional[int] = None
    status_desc: Optional[str] = None
    suffix: Optional[str] = None
    lark: Optional[Lark] = None
    wechat: Optional[Wechat] = None
    webSearch: Optional[WebSearch] = None
    filesState: Optional[List[FilesState]] = None


class QalibPositiveNegative(BaseModel):
    positives: Optional[List] = None
    negatives: Optional[List] = None


class QalibSample(QalibPositiveNegative):
    name: str
    featureStoreId: str
    confirmed: Optional[bool] = False


class Pipeline(BaseModel):
    webSearchToken: str
    featureStoreId: str
    confirmed: bool
    success: bool
    code: int
    status: str


class AddDocError(BaseModel):
    fileName: Optional[str]
    reason: Optional[str]


class AddDocsRes(BaseModel):
    docBase: Optional[str] = ''
    docs: Optional[List[str]] = []
    errors: Optional[List[AddDocError]] = []
