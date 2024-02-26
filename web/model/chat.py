from typing import Optional, List

from pydantic import BaseModel

from web.model.huixiangdou import HxdTaskChatHistory, ChatResponse


class ChatRequestBody(BaseModel):
    content: Optional[str] = ""
    images: Optional[List[str]] = []
    history: Optional[List[HxdTaskChatHistory]] = []


class ChatOnlineResponseBody(BaseModel):
    queryId: str


class ChatQueryInfo(BaseModel):
    featureStoreId: str
    queryId: str
    request: ChatRequestBody
    response: Optional[ChatResponse] = None
