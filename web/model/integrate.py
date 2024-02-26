from typing import Optional

from pydantic import BaseModel


class IntegrateLarkBody(BaseModel):
    webhookUrl: str
    appId: str
    appSecret: str
    encryptKey: str
    verificationToken: Optional[str] = ""


class IntegrateWebSearchBody(BaseModel):
    webSearchToken: str
    vendor: Optional[str] = ""
