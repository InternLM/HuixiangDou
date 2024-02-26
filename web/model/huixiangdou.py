from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class HxdToken(BaseModel):
    exp: int
    iat: float
    jti: str
    qa_name: str


class HxdTaskChatHistory(BaseModel):
    sender: int
    content: str


class HxdTaskPayload(BaseModel):
    name: Optional[str] = None
    feature_store_id: Optional[str] = None
    file_list: Optional[List[str]] = []
    file_abs_base: Optional[str] = None
    positive: Optional[List[str]] = []
    negative: Optional[List[str]] = []
    content: Optional[str] = None
    images: Optional[List[str]] = []
    history: Optional[List[HxdTaskChatHistory]] = []
    web_search_token: Optional[str] = None


class HxdTaskType(Enum):
    ADD_DOC = "add_doc"
    UPDATE_PIPELINE = "update_pipeline"
    UPDATE_SAMPLE = "update_sample"
    CHAT = "chat"


class HxdTask(BaseModel):
    type: HxdTaskType
    payload: HxdTaskPayload


class HxdTaskResponse(BaseModel):
    feature_store_id: Optional[str] = None
    code: Optional[int] = None
    status: Optional[str] = None
    type: Optional[str] = None


class ChatResponse(BaseModel):
    code: Optional[int] = -1
    state: Optional[str] = ""
    text: Optional[str] = ""
    references: Optional[list[str]] = []


class HxdChatResponse(BaseModel):
    feature_store_id: str
    query_id: str
    response: ChatResponse
