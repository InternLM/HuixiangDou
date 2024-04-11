import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from redis.lock import Lock

import web.constant.biz_constant as biz_const
from web.model.chat import ChatType
from web.model.huixiangdou import HxdChatResponse, HxdTaskResponse, HxdTaskType
from web.model.qalib import Pipeline, QalibInfo, QalibSample
from web.orm.redis import r
from web.service.agent import LarkAgent
from web.service.cache import ChatCache
from web.util.log import log

logger = log(__name__)
scheduler = AsyncIOScheduler()


def handle_task_add_doc_response(response: HxdTaskResponse):
    """update qalib's status from huixiangdou response's code.

    :param response:
    :return:
    """
    logger.info('do task: add doc')
    fid = response.feature_store_id
    name = biz_const.RDS_KEY_QALIB_INFO
    files_state = response.files_state
    o = r.hget(name=name, key=fid)
    if not o:
        logger.error(f"can't find {name}:{fid} in redis.")
        return
    qalib_info = QalibInfo(**json.loads(o))

    qalib_info.status = biz_const.HXD_PIPELINE_QALIB_CREATE_SUCCESS if response.code == 0 else response.code
    qalib_info.status_desc = response.status
    qalib_info.filesState = files_state

    r.hset(name=name, key=fid, value=qalib_info.model_dump_json())
    logger.info(
        f"do task={response.type} with fid={response.feature_store_id}'s result: {response.code}-{response.status}"
    )


def handle_task_update_sample_response(response: HxdTaskResponse):
    """update sample's confirm status from response's code.

    :param response:
    :return:
    """
    logger.info('do task: update sample')
    name = biz_const.RDS_KEY_SAMPLE_INFO
    fid = response.feature_store_id
    o = r.hget(name=name, key=fid)
    if not o:
        logger.error(f"can't find {name}:{fid} in redis")
        return
    sample = QalibSample(**json.loads(o))
    sample.confirmed = True if response.code == 0 else False
    r.hset(name=name, key=fid, value=sample.model_dump_json())


def handle_task_update_pipeline_response(response: HxdTaskResponse):
    logger.info('do task: update pipeline')
    name = biz_const.RDS_KEY_PIPELINE
    o = r.hget(name=name, key=response.feature_store_id)
    if not o:
        logger.error(f"can't find {name}:{response.feature_store_id} in redis")
        return
    pipeline = Pipeline(**json.loads(o))
    pipeline.status = response.status
    pipeline.code = response.code
    pipeline.confirmed = True
    pipeline.success = True if response.code == 0 else False
    r.hset(name=name,
           key=response.feature_store_id,
           value=pipeline.model_dump_json())


async def sync_hxd_task_response() -> None:
    """
    sync huixiangdou task response from redis and do relative process
    :return: None
    """
    o = r.lpop(biz_const.RDS_KEY_HXD_TASK_RESPONSE)
    if not o:
        logger.debug(
            f'lpop from {biz_const.RDS_KEY_HXD_TASK_RESPONSE} is empty')
        return
    hxd_task_response = HxdTaskResponse(**json.loads(o))
    if not hxd_task_response:
        logger.error(
            f'deserializing huixiangdou task response failed, raw: {o}')
        return
    task_type = hxd_task_response.type
    if task_type == HxdTaskType.ADD_DOC.value:
        handle_task_add_doc_response(hxd_task_response)
    elif task_type == HxdTaskType.UPDATE_SAMPLE.value:
        handle_task_update_sample_response(hxd_task_response)
    elif task_type == HxdTaskType.UPDATE_PIPELINE.value:
        handle_task_update_pipeline_response(hxd_task_response)
    else:
        logger.error(f'unrecognized task type: {task_type}')
    return


async def fetch_chat_response():
    name = biz_const.RDS_KEY_HXD_CHAT_RESPONSE
    length = r.llen(name)
    if length == 0:
        return

    while length > 0:
        length -= 1
        o = r.lpop(name)
        if not o:
            logger.debug(f'lpop for {name} is empty, omit')
            continue
        chat_response = HxdChatResponse(**json.loads(o))
        logger.info(
            f'[chat-response] feature_store_id: {chat_response.feature_store_id}, content: {chat_response.response.model_dump_json()}, query_id: {chat_response.query_id}'
        )
        query_info = ChatCache.set_query_response(
            chat_response.query_id, chat_response.feature_store_id,
            chat_response.response)

        if not query_info:
            continue
        if query_info.type == ChatType.ONLINE:
            continue
        if query_info.type == ChatType.LARK:
            await LarkAgent.response_callback(query_info)
        elif query_info.type == ChatType.WECHAT:
            pass


def allow_scheduler(task):
    lock = Lock(r, f'{biz_const.RDS_KEY_SCHEDULER}-{task}')
    if lock.acquire(blocking=False):
        logger.info(f'{biz_const.RDS_KEY_SCHEDULER}-{task} is locked')
        return True
    return False


def start_scheduler():
    if not scheduler.running:
        # ensure only one scheduler task is running
        # if allow_scheduler("sync_hxd_task_response"):
        logger.info('start scheduler of sync_hxd_task_respone')
        scheduler.add_job(sync_hxd_task_response,
                          IntervalTrigger(seconds=1))  # 100ms
        scheduler.add_job(fetch_chat_response, IntervalTrigger(seconds=1))
        # more scheduler job can be added here
        scheduler.start()


def release_scheduler_lock(task) -> bool:
    key = f'{biz_const.RDS_KEY_SCHEDULER}-{task}'
    r.delete(key)
    return False if r.exists(key) else True


def stop_scheduler():
    task_1 = 'sync_hxd_task_response'
    if release_scheduler_lock(task_1):
        logger.info(f'release scheduler lock of {task_1} successfully.')
    else:
        logger.error(
            f'release scheduler lock of {task_1} failed. you should delete this key from redis manually.'
        )
