from fastapi import Request, Response
from lark_oapi.adapter.flask import *

from web.service.agent import LarkAgent


class MessageService:

    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    def on_lark_message(self):
        rsp = LarkAgent.get_event_handler().do(parse_req())
        return parse_resp(rsp)

    def on_wechat_message(self):
        pass
