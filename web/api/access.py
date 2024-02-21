from fastapi import APIRouter, Response
from web.model.access import LoginBody
from web.service.access import LoginService

api = APIRouter()


@api.post("/v1/login")
async def login(body: LoginBody, response: Response):
    login_service = LoginService(body, response)
    return await login_service.login()
