from pydantic import BaseModel


class LoginBody(BaseModel):
    name: str
    password: str


class AccessInfo(BaseModel):
    hashpass: str
    featureStoreId: str
