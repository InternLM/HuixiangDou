from pydantic import BaseModel


class HxdToken(BaseModel):
    exp: int
    iat: float
    jti: str
    qa_name: str
