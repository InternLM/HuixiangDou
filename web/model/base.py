from fastapi import HTTPException
from pydantic import BaseModel, Field


class BaseBody(BaseModel):
    msg: str = Field(default="ok")
    msgCode: str = Field(default="10000")
    data: object = None


def standard_error_response(error: dict, data=None) -> BaseBody:
    if not data:
        data = {}
    return BaseBody(msg=error.get("msg"), msgCode=error.get("code"), data=data)
