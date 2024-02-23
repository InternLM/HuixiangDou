import json
import os.path

from web.model.base import BaseBody
from web.model.qalib import QalibInfo, QalibPositiveNegative, QalibSample
from web.model.statistic import StatisticTotal
from web.orm.redis import r
from web.util.log import log
import web.util.str as str_util
import web.constant.biz_constant as biz_const
from fastapi import Response, Request, File, UploadFile
from web.model.hxd_token import HxdToken
from typing import List, Union

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
        file_paths = []
        total_bytes = int(self.request.headers.get("content-length"))
        write_size = 0
        # print can be removed if performance matters
        for file in files:
            write_path = os.path.join(store_dir, file.filename)
            with open(write_path, "wb") as f:
                while True:
                    chunk = await file.read(32768)  # 64KB
                    if not chunk:
                        break
                    f.write(chunk)
                    write_size += len(chunk)
                    progress = (write_size / total_bytes) * 100
                    print(f"\rQalib({hxd_token.qa_name}) total process: {progress:.2f}%", end="")
            file_paths.append(write_path)
            await file.close()
        return BaseBody(
            data={"files": file_paths}
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
        r.hset(name=biz_const.RDS_KEY_SAMPLE_INFO, key=hxd_token.jti, value=qalib_sample.model_dump_json())
        return await self.get_sample_info()

    async def info_statistic(self):
        qalib_total = r.hlen(biz_const.RDS_KEY_QALIB_INFO)
        # todo more statistic data will be added
        data = StatisticTotal(qalibTotal=qalib_total)
        return BaseBody(
            data=data
        )


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
