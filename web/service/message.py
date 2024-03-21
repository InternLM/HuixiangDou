from fastapi import Request, Response

from web.model.base import BaseBody
from web.model.chat import WechatRequest
from web.service.agent import LarkAgent, WechatAgent


class MessageService:

    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    async def on_lark_message(self):
        req = await LarkAgent.parse_req(self.request)
        rsp = LarkAgent.get_event_handler().do(req)
        return LarkAgent.parse_rsp(rsp)

    async def on_wechat_message(self, body: WechatRequest, suffix: str):
        rsp = WechatAgent.action(body, suffix)
        if isinstance(rsp, BaseBody):
            return rsp
        return BaseBody(data=rsp)
