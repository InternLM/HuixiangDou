import base64
import hashlib
import json
import time
from typing import Union

from fastapi import Request, Response

from web.constant import biz_constant
from web.model.base import BaseBody, standard_error_response
from web.model.chat import ChatRequestBody, ChatQueryInfo, ChatOnlineResponseBody
from web.model.huixiangdou import HxdTask, HxdTaskType, HxdTaskPayload, ChatResponse
from web.model.qalib import QalibInfo
from web.mq.hxd_task import HuixiangDouTask
from web.orm.redis import r
from web.service.qalib import get_store_dir
from web.util.log import log

logger = log(__name__)


class ChatService:
    def __init__(self, request: Request, response: Response, hxd_info: QalibInfo):
        self.hxd_info = hxd_info
        self.request = request
        self.response = response

    async def chat_online(self, body: ChatRequestBody):
        feature_store_id = self.hxd_info.featureStoreId
        query_id = self._generate_query_id(body.content)
        logger.info(
            f"[chat-request]/online feature_store_id: {feature_store_id}, content: {body.content}, query_id: {query_id}")

        # store images
        images_path = []
        if len(body.images) > 0:
            images_path = self._store_images(body.images, query_id)

        task = HxdTask(
            type=HxdTaskType.CHAT,
            payload=HxdTaskPayload(feature_store_id=feature_store_id, query_id=query_id, content=body.content,
                                   history=body.history, images=images_path)
        )
        if HuixiangDouTask().updateTask(task):
            chat_query_info = ChatQueryInfo(featureStoreId=feature_store_id, queryId=query_id,
                                            request=ChatRequestBody(content=body.content, images=images_path,
                                                                    history=body.history))
            ChatCache().set_query_request(query_id, feature_store_id, chat_query_info)
            return BaseBody(data=ChatOnlineResponseBody(queryId=query_id))

        return standard_error_response(biz_constant.ERR_CHAT)

    async def fetch_response(self, body: ChatOnlineResponseBody):
        feature_store_id = self.hxd_info.featureStoreId
        info = ChatCache().get_query_info(body.queryId, feature_store_id)
        if not info:
            return standard_error_response(biz_constant.ERR_NOT_EXIST_CHAT)
        if not info.response:
            return standard_error_response(biz_constant.CHAT_STILL_IN_QUEUE)
        return BaseBody(data=info.response)

    def _generate_query_id(self, content):
        feature_store_id = self.hxd_info.featureStoreId
        raw = feature_store_id + content + str(time.time())
        h = hashlib.sha3_512()
        h.update(raw.encode("utf-8"))
        q = h.hexdigest()
        return q[0:8]

    def _store_images(self, images, query_id):
        feature_store_id = self.hxd_info.featureStoreId
        image_store_dir = get_store_dir(feature_store_id)
        if not image_store_dir:
            logger.error(f"get store dir failed for: {feature_store_id}")
            return []

        image_store_dir += "/images/"
        ret = []

        index = 0
        for image in images:
            decoded_image = base64.b64decode(image)
            store_path = image_store_dir + query_id[-8:] + "_" + str(index)
            with open(store_path, "wb") as f:
                f.write(decoded_image)
            ret.append(store_path)
        return ret


class ChatCache:
    def __init__(self):
        pass

    @classmethod
    def set_query_request(cls, query_id: str, feature_store_id: str, info: ChatQueryInfo):
        cls._set_query_info(query_id, feature_store_id, info)

    @classmethod
    def set_query_response(cls, query_id: str, feature_store_id: str, response: ChatResponse):
        q = cls.get_query_info(query_id, feature_store_id)
        if not q:
            return
        q.response = response
        cls._set_query_info(query_id, feature_store_id, q)

    @classmethod
    def get_query_info(cls, query_id: str, feature_store_id: str) -> Union[ChatQueryInfo, None]:
        key = biz_constant.RDS_KEY_QUERY_INFO + "-" + feature_store_id
        field = query_id
        o = r.hget(key, field)
        if not o or len(o) == 0:
            logger.error(f"feature_store_id: {feature_store_id} get query: {query_id} empty, omit")
            return None

        return ChatQueryInfo(**json.loads(o))

    @classmethod
    def _set_query_info(cls, query_id: str, feature_store_id: str, info: ChatQueryInfo):
        key = biz_constant.RDS_KEY_QUERY_INFO + "-" + feature_store_id
        field = query_id
        r.hset(key, field, info.model_dump_json())
