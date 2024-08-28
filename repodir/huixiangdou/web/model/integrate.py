from typing import Optional

from pydantic import BaseModel


class IntegrateLarkBody(BaseModel):
    appId: str
    appSecret: str


class IntegrateWebSearchBody(BaseModel):
    webSearchToken: str
    vendor: Optional[str] = ''
