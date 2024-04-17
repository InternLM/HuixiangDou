from __future__ import annotations

import json
import os.path
from typing import List, Union

from fastapi import File, Request, Response, UploadFile

import web.constant.biz_constant as biz_const
import web.util.str as str_util
from web.config.env import HuixiangDouEnv
from web.model.base import BaseBody, standard_error_response
from web.model.huixiangdou import (HxdTask, HxdTaskPayload, HxdTaskType,
                                   HxdToken)
from web.model.integrate import IntegrateLarkBody, IntegrateWebSearchBody
from web.model.qalib import (AddDocError, AddDocsRes, Lark, QalibInfo,
                             QalibPositiveNegative, QalibSample, WebSearch,
                             Wechat)
from web.mq.hxd_task import HuixiangDouTask
from web.orm.redis import r
from web.util.log import log

logger = log(__name__)


def get_hxd_token_by_cookie(cookies) -> Union[HxdToken, None]:
    return HxdToken(
        **(str_util.parse_jwt(cookies.get(biz_const.HXD_COOKIE_KEY))
           )) if cookies and cookies.get(biz_const.HXD_COOKIE_KEY) else None


def get_store_dir(feature_store_id: str) -> Union[str, None]:
    if not feature_store_id:
        return None
    try:
        crt_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(os.path.dirname(crt_path))
        qa_path = os.path.join(parent_path, f'qa/{feature_store_id}')
        os.makedirs(qa_path, exist_ok=True)
        return qa_path
    except Exception as e:
        logger.error(f'{e}')
        return None


def get_wechat_on_message_url(suffix: str) -> str:
    endpoint = HuixiangDouEnv.get_message_endpoint()
    return endpoint + 'api/v1/message/v1/wechat/' + suffix


def get_lark_on_message_url() -> str:
    endpoint = HuixiangDouEnv.get_message_endpoint()
    return endpoint + 'api/v1/message/v1/lark'


def gen_suffix(feature_store_id: str) -> str:
    length = biz_const.HXD_FEATURE_STORE_SUFFIX_LENGTH
    if len(feature_store_id) <= length:
        return feature_store_id
    return feature_store_id[-length:]


def get_suffix_by_name(name: str) -> Union[str, None]:
    length = biz_const.HXD_FEATURE_STORE_SUFFIX_LENGTH
    if len(name) < length:
        logger.error(
            f'group name: {name} shorter than suffix length, remind check group name'
        )
        return None

    return name[-length:]


class QaLibService:

    def __init__(self, request: Request, response: Response,
                 hxd_info: QalibInfo):
        self.request = request
        self.response = response
        self.hxd_info = hxd_info

    @classmethod
    def get_existed_docs(cls, feature_store_id) -> List:
        o = r.hget(name=biz_const.RDS_KEY_QALIB_INFO, key=feature_store_id)
        if not o:
            return []
        qalib_info = QalibInfo(**json.loads(o))
        return qalib_info.docs

    async def info(self) -> BaseBody:
        return BaseBody(data=self.hxd_info)

    async def add_docs(self, files: List[UploadFile] = File(...)):
        feature_store_id = self.hxd_info.featureStoreId
        name = self.hxd_info.name
        logger.info(f'start to add docs for qalib: {name}')

        store_dir = get_store_dir(feature_store_id)
        if not files or not store_dir:
            return BaseBody()

        ret = AddDocsRes(errors=[])
        docs = self.get_existed_docs(feature_store_id)

        total_bytes = int(self.request.headers.get('content-length'))
        if total_bytes > biz_const.HXD_ADD_DOCS_ONCE_MAX:
            return standard_error_response(
                biz_const.ERR_QALIB_ADD_DOCS_ONCE_MAX)
        write_size = 0
        # store files
        for file in files:
            if file.filename and len(file.filename.encode('utf-8')) > 255:
                logger.error(
                    f'filename: {file.filename} too long, maximum 255 bytes, omit current filename'
                )
                ret.errors.append(
                    AddDocError(fileName=file.filename,
                                reason='filename is too long'))
                continue

            with open(os.path.join(store_dir, file.filename), 'wb') as f:
                while True:
                    chunk = await file.read(32768)  # 64KB
                    if not chunk:
                        break
                    f.write(chunk)
                    write_size += len(chunk)
                    progress = (write_size / total_bytes) * 100
                    # print can be removed if performance matters
                    print(f'\rQalib({name}) total process: {progress:.2f}%',
                          end='')
            docs.append(file.filename)
            await file.close()
        # update qalib in redis
        if not QaLibCache().update_qalib_docs(feature_store_id, docs,
                                              store_dir):
            return BaseBody()
        # update to huixiangdou task queue
        if not HuixiangDouTask().updateTask(
                HxdTask(type=HxdTaskType.ADD_DOC,
                        payload=HxdTaskPayload(
                            name=name,
                            feature_store_id=feature_store_id,
                            file_list=docs,
                            file_abs_base=store_dir))):
            return BaseBody()

        ret.docBase = store_dir
        ret.docs = docs
        return BaseBody(data=ret)

    async def get_sample_info(self):
        sample_info = QaLibCache.get_sample_info(self.hxd_info.featureStoreId)
        return BaseBody(data=sample_info)

    async def update_sample_info(self, body: QalibPositiveNegative):
        name = self.hxd_info.name
        feature_store_id = self.hxd_info.featureStoreId

        positives = body.positives
        negatives = body.negatives
        qalib_sample = QalibSample(name=name,
                                   featureStoreId=feature_store_id,
                                   positives=positives,
                                   negatives=negatives,
                                   confirmed=False)
        # update sample to redis
        QaLibCache.set_sample_info(feature_store_id, qalib_sample)
        # update sample to huixiangdou task
        if not HuixiangDouTask().updateTask(
                HxdTask(type=HxdTaskType.UPDATE_SAMPLE,
                        payload=HxdTaskPayload(
                            name=name,
                            feature_store_id=feature_store_id,
                            positive=positives,
                            negative=negatives))):
            return BaseBody()
        return await self.get_sample_info()

    async def integrate_lark(self, body: IntegrateLarkBody):
        feature_store_id = self.hxd_info.featureStoreId
        info = QaLibCache.get_qalib_info(feature_store_id)
        if not info:
            return standard_error_response(biz_const.ERR_QALIB_INFO_NOT_FOUND)

        if info.lark:
            info.lark.appId = body.appId
            info.lark.appSecret = body.appSecret
        else:
            info.lark = Lark(
                appId=body.appId,
                appSecret=body.appSecret,
                encryptKey=HuixiangDouEnv.get_lark_encrypt_key(),
                verificationToken=HuixiangDouEnv.get_lark_verification_token(),
                eventUrl=get_lark_on_message_url())
        QaLibCache.set_qalib_info(feature_store_id, info)
        QaLibCache.set_lark_info(body.appId, body.appSecret)
        return BaseBody(data=info.lark)

    async def integrate_web_search(self, body: IntegrateWebSearchBody):
        feature_store_id = self.hxd_info.featureStoreId
        info = QaLibCache.get_qalib_info(feature_store_id)
        if not info:
            return standard_error_response(biz_const.ERR_QALIB_INFO_NOT_FOUND)

        info.webSearch = WebSearch(token=body.webSearchToken)

        task = HxdTask(type=HxdTaskType.UPDATE_PIPELINE,
                       payload=HxdTaskPayload(
                           feature_store_id=feature_store_id,
                           name=self.hxd_info.name,
                           web_search_token=body.webSearchToken))
        if HuixiangDouTask().updateTask(task):
            QaLibCache.set_qalib_info(feature_store_id, info)
            return BaseBody()

        return standard_error_response(biz_const.ERR_INFO_UPDATE_FAILED)


class QaLibCache:

    def __init__(self):
        pass

    @classmethod
    def get_qalib_info(cls, feature_store_id: str) -> Union[QalibInfo, None]:
        name = biz_const.RDS_KEY_QALIB_INFO
        key = feature_store_id
        o = r.hget(name, key)
        if not o:
            logger.error(
                f'[qalib] feature_store_id: {feature_store_id}, get info empty'
            )
            return None
        return QalibInfo(**json.loads(o))

    @classmethod
    def set_qalib_info(cls, feature_store_id: str, info: QalibInfo):
        name = biz_const.RDS_KEY_QALIB_INFO
        key = feature_store_id
        return r.hset(name, key, info.model_dump_json()) == 1

    @classmethod
    def init_qalib_info(cls, feature_store_id: str, status: int, name: str,
                        suffix: str) -> bool:
        """add qalib info to qalib:info db.

        :param name:
        :param feature_store_id:
        :param status:
        :return:
        """
        wechat = Wechat(onMessageUrl=get_wechat_on_message_url(suffix))
        lark = Lark(
            encryptKey=HuixiangDouEnv.get_lark_encrypt_key(),
            verificationToken=HuixiangDouEnv.get_lark_verification_token(),
            eventUrl=get_lark_on_message_url())
        qalib_info = QalibInfo(featureStoreId=feature_store_id,
                               status=status,
                               name=name,
                               wechat=wechat,
                               lark=lark,
                               suffix=suffix)
        if not cls.set_qalib_info(feature_store_id, qalib_info):
            logger.error(
                f'[qalib] feature_store_id: {feature_store_id}, init qalib info failed'
            )
            r.hdel(biz_const.RDS_KEY_QALIB_INFO, feature_store_id)
            return False
        return True

    @classmethod
    def del_qalib_info(cls, feature_store_id: str) -> bool:
        """del qalib info to qalib:info db.

        :param feature_store_id:
        :return:
        """
        return True if r.hdel(biz_const.RDS_KEY_QALIB_INFO,
                              feature_store_id) == 1 else False

    @classmethod
    def update_qalib_docs(cls, feature_store_id: str, added_docs: List[str],
                          file_base: str) -> bool:
        """update qalib's docs.

        :param feature_store_id:
        :param added_docs:
        :param file_base:
        :return:
        """
        try:
            info = cls.get_qalib_info(feature_store_id)
            if not info:
                return False

            raw_docs = info.docs
            if not raw_docs:
                raw_docs = []
            raw_docs.extend(added_docs)
            info.docs = list(set(raw_docs))
            info.docBase = file_base

            cls.set_qalib_info(feature_store_id, info)
            return True
        except Exception as e:
            logger.error(
                f'[qalib] feature_store_id: {feature_store_id}, update docs failed: {e}'
            )
            return False

    @classmethod
    def get_sample_info(cls,
                        feature_store_id: str) -> Union[QalibSample, None]:
        o = r.hget(name=biz_const.RDS_KEY_SAMPLE_INFO, key=feature_store_id)
        if not o:
            logger.info(
                f'[qalib] feature_store_id: {feature_store_id}, get empty sample'
            )
            return None
        return QalibSample(**json.loads(o))

    @classmethod
    def set_sample_info(cls, feature_store_id: str, sample_info: QalibSample):
        r.hset(name=biz_const.RDS_KEY_SAMPLE_INFO,
               key=feature_store_id,
               value=sample_info.model_dump_json())

    @classmethod
    def set_suffix_to_qalib(cls, suffix: str, feature_store_id: str):
        r.hset(name=biz_const.RDS_KEY_SUFFIX_TO_QALIB,
               key=suffix,
               value=feature_store_id)

    @classmethod
    def get_qalib_feature_store_id_by_suffix(cls,
                                             suffix: str) -> Union[str, None]:
        o = r.hget(name=biz_const.RDS_KEY_SUFFIX_TO_QALIB, key=suffix)
        if not o:
            logger.error(f'[qalib] suffix: {suffix} has no qalib')
            return None
        return o.decode('utf-8')

    @classmethod
    def get_lark_info_by_app_id(cls, app_id: str) -> Union[str, None]:
        key = biz_const.RDS_KEY_LARK_CONFIG + ':' + app_id
        o = r.get(key)
        if not o:
            logger.error(f'f[lark] app_id: {app_id} has no record')
            return None
        return o.decode('utf-8')

    @classmethod
    def set_lark_info(cls, app_id: str, app_secret: str):
        key = biz_const.RDS_KEY_LARK_CONFIG + ':' + app_id
        r.set(key, app_secret)
