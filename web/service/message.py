from fastapi import Request, Response


class MessageService:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    def on_lark_message(self):
        pass

    def on_wechat_message(self):
        pass
