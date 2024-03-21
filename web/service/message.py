from fastapi import Request, Response
from lark_oapi.adapter.flask import parse_req, parse_resp

from web.model.base import BaseBody
from web.model.chat import WechatRequest
from web.service.agent import LarkAgent, WechatAgent


class MessageService:

    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    def on_lark_message(self):
        rsp = LarkAgent.get_event_handler().do(parse_req())
        return parse_resp(rsp)

    async def on_wechat_message(self, body: WechatRequest, suffix: str):
        rsp = WechatAgent.action(body, suffix)
        if isinstance(rsp, BaseBody):
            return rsp
        return BaseBody(data=rsp)
