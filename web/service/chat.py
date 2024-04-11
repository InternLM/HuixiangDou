import base64
import binascii
import hashlib
import os
import time
from typing import List, Union

from fastapi import Request, Response

from web.constant import biz_constant
from web.model.base import BaseBody, Image, standard_error_response
from web.model.chat import (ChatCaseFeedbackBody, ChatOnlineResponseBody,
                            ChatQueryInfo, ChatRequestBody, ChatType)
from web.model.huixiangdou import HxdTask, HxdTaskPayload, HxdTaskType
from web.model.qalib import QalibInfo
from web.mq.hxd_task import HuixiangDouTask
from web.service.cache import ChatCache
from web.service.qalib import get_store_dir
from web.util.image import detect_base64_image_suffix
from web.util.log import log

logger = log(__name__)


class ChatService:

    def __init__(self, request: Request, response: Response,
                 hxd_info: QalibInfo):
        self.hxd_info = hxd_info
        self.request = request
        self.response = response

    async def chat_online(self, body: ChatRequestBody):
        feature_store_id = self.hxd_info.featureStoreId
        query_id = self.generate_query_id(body.content)
        logger.info(
            f'[chat-request]/online feature_store_id: {feature_store_id}, content: {body.content}, query_id: {query_id}'
        )

        # store images
        images_path = []
        if len(body.images) > 0:
            images_path = self._store_images(body.images, query_id)
            if len(images_path) == 0:
                return standard_error_response(biz_constant.ERR_CHAT)

        task = HxdTask(type=HxdTaskType.CHAT,
                       payload=HxdTaskPayload(
                           feature_store_id=feature_store_id,
                           query_id=query_id,
                           content=body.content,
                           history=body.history,
                           images=images_path))
        if HuixiangDouTask().updateTask(task):
            chat_query_info = ChatQueryInfo(featureStoreId=feature_store_id,
                                            queryId=query_id,
                                            request=ChatRequestBody(
                                                content=body.content,
                                                images=images_path,
                                                history=body.history,
                                                type=ChatType.ONLINE))
            ChatCache.set_query_request(query_id, feature_store_id,
                                        chat_query_info)
            ChatCache.mark_unique_inference_user(feature_store_id,
                                                 ChatType.ONLINE)
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

    def chat_by_agent(self,
                      body: ChatRequestBody,
                      t: ChatType,
                      chat_detail: object,
                      user_unique_id: str,
                      query_id: str = None) -> bool:
        feature_store_id = self.hxd_info.featureStoreId
        if not query_id:
            query_id = self.generate_query_id(body.content)
        logger.info(
            f'[chat-request]/agent feature_store_id: {feature_store_id}, content: {body.content}, query_id: {query_id}, type:{t}'
        )

        task = HxdTask(type=HxdTaskType.CHAT,
                       payload=HxdTaskPayload(
                           feature_store_id=feature_store_id,
                           query_id=query_id,
                           content=body.content,
                           history=body.history,
                           images=body.images))
        if HuixiangDouTask().updateTask(task):
            chat_query_info = ChatQueryInfo(featureStoreId=feature_store_id,
                                            queryId=query_id,
                                            request=ChatRequestBody(
                                                content=body.content,
                                                images=body.images,
                                                history=body.history),
                                            type=t,
                                            detail=chat_detail)
            ChatCache.set_query_request(query_id, feature_store_id,
                                        chat_query_info)
            ChatCache.mark_unique_inference_user(user_unique_id, t)
            return True

        return False

    def generate_query_id(self, content):
        feature_store_id = self.hxd_info.featureStoreId
        raw = feature_store_id + content[-8:] + str(time.time())
        h = hashlib.sha3_512()
        h.update(raw.encode('utf-8'))
        q = h.hexdigest()
        return q[0:8]

    def _store_images(self, images, query_id) -> List[str]:
        feature_store_id = self.hxd_info.featureStoreId
        image_store_dir = get_store_dir(feature_store_id)
        if not image_store_dir:
            logger.error(f'get store dir failed for: {feature_store_id}')
            return []

        image_store_dir += '/images/'
        os.makedirs(image_store_dir, exist_ok=True)
        ret = []

        index = 0
        for image in images:
            try:
                while len(image) % 4 != 0:
                    image += '='
                [image_format, image] = detect_base64_image_suffix(image)
                if image_format == Image.INVALID:
                    logger.error(f'invalid image format, query_id: {query_id}')
                    return []
                decoded_image = base64.b64decode(image)
            except binascii.Error:
                logger.error(
                    f'invalid base64 encoded image, query_id: {query_id}')
                return []
            store_path = image_store_dir + query_id[-8:] + '_' + str(
                index) + '.' + image_format.value
            with open(store_path, 'wb') as f:
                f.write(decoded_image)
            ret.append(store_path)
        return ret

    def gen_image_store_path(self, query_id, name: str,
                             agent: ChatType) -> Union[str, None]:
        feature_store_id = self.hxd_info.featureStoreId
        image_store_dir = get_store_dir(feature_store_id)
        if not image_store_dir:
            logger.error(f'get store dir failed for: {feature_store_id}')
            return None

        image_store_dir += '/images/'
        os.makedirs(name=image_store_dir, exist_ok=True)
        return image_store_dir + agent.name + query_id[-8:] + '_' + name

    async def case_feedback(self, body: ChatCaseFeedbackBody):
        feature_store_id = self.hxd_info.featureStoreId
        query_id = body.queryId
        query_info = ChatCache.get_query_info(query_id, feature_store_id)
        if not query_info:
            return standard_error_response(biz_constant.ERR_CHAT_CASE_FEEDBACK)
        return BaseBody() \
            if ChatCache.update_case_feedback(feature_store_id, body.type, query_info.model_dump_json()) \
            else standard_error_response(biz_constant.ERR_CHAT_CASE_FEEDBACK)
