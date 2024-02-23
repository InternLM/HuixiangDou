import json
import os.path

from web.model.base import BaseBody
from web.model.qalib import QalibInfo, QalibPositiveNegative, QalibSample
from web.orm.redis import r
from web.util.log import log
import web.util.str as str_util
import web.constant.biz_constant as biz_const
from fastapi import Response, Request, File, UploadFile
from web.model.huixiangdou import HxdToken, HxdTask, HxdTaskType, HxdTaskPayload
from typing import List, Union
from web.mq.hxd_task import HuixiangDouTask

logger = log(__name__)


def get_hxd_token_by_cookie(cookies) -> Union[HxdToken, None]:
    return HxdToken(**(
        str_util.parse_jwt(
            cookies.get(biz_const.HXD_COOKIE_KEY)
        )
    )) if cookies and cookies.get(biz_const.HXD_COOKIE_KEY) else None


def get_store_dir(feature_store_id: str) -> Union[str, None]:
    if not feature_store_id:
        return None
    try:
        crt_path = os.path.abspath(__file__)
        parent_path = os.path.dirname(os.path.dirname(crt_path))
        qa_path = os.path.join(parent_path, f"qa/{feature_store_id}")
        os.makedirs(qa_path, exist_ok=True)
        return qa_path
    except Exception as e:
        logger.error(f"{e}")
        return None


def add_qalib_info(fid: str, status: int, name: str) -> bool:
    """
    add qalib info to qalib:info db
    :param name:
    :param fid:
    :param status:
    :return:
    """
    qalib_info = QalibInfo(featureStoreId=fid, status=status, name=name)
    if 1 != r.hset(name=biz_const.RDS_KEY_QALIB_INFO, key=fid, value=qalib_info.model_dump_json()):
        logger.error("init qalib info failed")
        r.hdel(biz_const.RDS_KEY_QALIB_INFO, fid)
        return False
    return True


def del_qalib_info(fid: str) -> bool:
    """
    del qalib info to qalib:info db
    :param fid:
    :return:
    """
    return True if r.hdel(biz_const.RDS_KEY_QALIB_INFO, fid) == 1 else False


def update_qalib_docs(fid: str, added_docs: List[str], file_base: str) -> bool:
    """
    update qalib's docs
    :param fid:
    :param added_docs:
    :param file_base:
    :return:
    """
    try:
        o = r.hget(biz_const.RDS_KEY_QALIB_INFO, fid)
        if not o:
            logger.error(f"qalib({fid}) is not existed.")
            return False
        info = QalibInfo(**json.loads(o))
        raw_docs = info.docs
        if not raw_docs:
            raw_docs = []
        raw_docs.extend(added_docs)
        info.docs = list(set(raw_docs))
        info.docBase = file_base
        r.hset(biz_const.RDS_KEY_QALIB_INFO, fid, info.model_dump_json())
        return True
    except Exception as e:
        logger.error(f"{e}")
        return False


class QaLibService:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    async def info(self) -> BaseBody:
        hxd_token = get_hxd_token_by_cookie(self.request.cookies)
        if not hxd_token or not hxd_token.jti:
            return BaseBody(
                msg=biz_const.ERR_QALIB_API_NO_ACCESS.get("msg"),
                msgCode=biz_const.ERR_QALIB_API_NO_ACCESS.get("code")
            )
        o = r.hget(biz_const.RDS_KEY_QALIB_INFO, hxd_token.jti)
        return BaseBody(
            data=None if not o else json.loads(o)
        )

    async def add_docs(self, files: List[UploadFile] = File(...)):
        hxd_token = get_hxd_token_by_cookie(self.request.cookies)
        logger.info(f"start to upload qalib({hxd_token.qa_name})")
        if not hxd_token or not hxd_token.jti:
            return BaseBody(
                msg=biz_const.ERR_QALIB_API_NO_ACCESS.get("msg"),
                msgCode=biz_const.ERR_QALIB_API_NO_ACCESS.get("code")
            )
        store_dir = get_store_dir(hxd_token.jti)
        if not files or not store_dir:
            return BaseBody()
        docs = []
        total_bytes = int(self.request.headers.get("content-length"))
        write_size = 0
        # store files
        for file in files:
            with open(os.path.join(store_dir, file.filename), "wb") as f:
                while True:
                    chunk = await file.read(32768)  # 64KB
                    if not chunk:
                        break
                    f.write(chunk)
                    write_size += len(chunk)
                    progress = (write_size / total_bytes) * 100
                    # print can be removed if performance matters
                    print(f"\rQalib({hxd_token.qa_name}) total process: {progress:.2f}%", end="")
            docs.append(file.filename)
            await file.close()
        # update qalib in redis
        if not update_qalib_docs(hxd_token.jti, docs, store_dir):
            return BaseBody()
        # update to huixiangdou task queue
        if not HuixiangDouTask().updateTask(
                HxdTask(
                    type=HxdTaskType.ADD_DOC,
                    payload=HxdTaskPayload(
                        name=hxd_token.qa_name,
                        feature_store_id=hxd_token.jti,
                        file_list=docs,
                        file_abs_base=store_dir
                    )
                )
        ):
            return BaseBody()

        return BaseBody(
            data={
                "docBase": store_dir,
                "docs": docs
            }
        )

    async def get_sample_info(self):
        hxd_token = get_hxd_token_by_cookie(self.request.cookies)
        if not hxd_token or not hxd_token.jti:
            return BaseBody(
                msg=biz_const.ERR_QALIB_API_NO_ACCESS.get("msg"),
                msgCode=biz_const.ERR_QALIB_API_NO_ACCESS.get("code")
            )
        o = r.hget(name=biz_const.RDS_KEY_SAMPLE_INFO, key=hxd_token.jti)
        return BaseBody(
            data=None if not o else json.loads(o)
        )

    async def update_sample_info(self, body: QalibPositiveNegative):
        hxd_token = get_hxd_token_by_cookie(self.request.cookies)
        if not hxd_token or not hxd_token.jti:
            return BaseBody(
                msg=biz_const.ERR_QALIB_API_NO_ACCESS.get("msg"),
                msgCode=biz_const.ERR_QALIB_API_NO_ACCESS.get("code")
            )
        positives = body.positives
        negatives = body.negatives
        qalib_sample = QalibSample(name=hxd_token.qa_name, featureStoreId=hxd_token.jti, positives=positives,
                                   negatives=negatives)
        # update sample to redis
        r.hset(name=biz_const.RDS_KEY_SAMPLE_INFO, key=hxd_token.jti, value=qalib_sample.model_dump_json())
        # update sample to huixiangdou task
        if not HuixiangDouTask().updateTask(
                HxdTask(
                    type=HxdTaskType.UPDATE_SAMPLE,
                    payload=HxdTaskPayload(
                        name=hxd_token.qa_name,
                        feature_store_id=hxd_token.jti,
                        positive=positives,
                        negative=negatives
                    )
                )
        ):
            return BaseBody()
        return await self.get_sample_info()

