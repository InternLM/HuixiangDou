from fastapi import APIRouter, Request, Response

from web.model.access import LoginBody
from web.service.access import LoginService

access_api = APIRouter()


@access_api.post('/v1/login')
async def login(body: LoginBody, request: Request, response: Response):
    return await LoginService(body, request, response).login()
