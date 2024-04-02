from fastapi import APIRouter, Request, Response

from web.model.chat import WechatRequest
from web.service.message import MessageService

message_api = APIRouter()


@message_api.post('/v1/lark')
async def on_lark_message(request: Request, response: Response):
    return await MessageService(request, response).on_lark_message()


@message_api.post('/v1/wechat/{suffix}')
async def on_wechat_message(request: Request, response: Response, suffix: str,
                            body: WechatRequest):
    return await MessageService(request,
                                response).on_wechat_message(body, suffix)
