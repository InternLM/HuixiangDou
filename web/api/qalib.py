from fastapi import APIRouter, Response, Request
from web.service.qalib import QaLibService

qalib_api = APIRouter()


@qalib_api.post("/v1/info")
async def qalib_info(request: Request, response: Response):
    return await QaLibService(request, response).info()
