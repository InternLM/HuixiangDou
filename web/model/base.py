from pydantic import BaseModel, Field


class BaseBody(BaseModel):
    msg: str = Field(default="success")
    msgCode: str = Field(default="10000")
    data: object = None

