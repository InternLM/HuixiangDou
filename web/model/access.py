from pydantic import BaseModel


class LoginBody(BaseModel):
    name: str
    password: str
