from pydantic import BaseModel, Field


class BaseBody(BaseModel):
    msg: str = Field(default="ok")
    msgCode: str = Field(default="10000")
    data: object = None

