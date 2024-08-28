from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, RootModel

from web.model.huixiangdou import ChatResponse, HxdTaskChatHistory


class ChatRequestBody(BaseModel):
    content: Optional[str] = ''
    images: Optional[List[str]] = []
    history: Optional[List[HxdTaskChatHistory]] = []


class ChatOnlineResponseBody(BaseModel):
    queryId: str


class ChatType(Enum):
    LARK = 0
    WECHAT = 1
    ONLINE = 2


class ChatQueryInfo(BaseModel):
    featureStoreId: str
    queryId: str
    type: Optional[ChatType] = ChatType.ONLINE
    request: ChatRequestBody
    response: Optional[ChatResponse] = None
    detail: Optional[object] = {}


class ChatCaseType(Enum):
    GOOD_CASE = 'good'
    BAD_CASE = 'bad'


class ChatCaseFeedbackBody(BaseModel):
    queryId: str
    type: ChatCaseType


class LarkChatDetail(BaseModel):
    appId: Optional[str] = ''
    appSecret: Optional[str] = ''
    messageId: Optional[str] = ''


class WechatType(Enum):
    TEXT = 'text'
    Image = 'image'
    Poll = 'poll'


class WechatQuery(BaseModel):
    type: WechatType
    content: Optional[str] = ''


class WechatRequest(BaseModel):
    query_id: Optional[str] = ''
    groupname: Optional[str] = ''
    username: Optional[str] = ''
    query: Optional[WechatQuery] = {}


class WechatResponse(RootModel):
    root: Optional[object] = []


class WechatPollItem(BaseModel):
    req: WechatRequest
    rsp: ChatResponse
