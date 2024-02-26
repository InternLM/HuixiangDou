import json

from web.util.log import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from web.orm.redis import r
import web.constant.biz_constant as biz_const
from web.model.huixiangdou import HxdTaskResponse, HxdTaskType
from redis.lock import Lock
from web.model.qalib import QalibInfo, QalibSample

logger = log(__name__)
scheduler = AsyncIOScheduler()


def do_task_add_doc(response: HxdTaskResponse):
    """
    update qalib's status from huixiangdou response's code
    :param response:
    :return:
    """
    logger.info("do task: add doc")
    fid = response.feature_store_id
    name = biz_const.RDS_KEY_QALIB_INFO
    o = r.hget(name=name, key=fid)
    if not o:
        logger.error(f"can't find {name}:{fid} in redis.")
        return
    qalib_info = QalibInfo(**json.loads(o))
    qalib_info.status = response.code
    r.hset(name=name, key=fid, value=qalib_info.model_dump_json())
    logger.info(f"do task={response.type} with fid={response.feature_store_id}'s result: {response.status}")


def do_task_update_sample(response: HxdTaskResponse):
    """
    update sample's confirm status from response's code
    :param response:
    :return:
    """
    logger.info("do task: update sample")
    name = biz_const.RDS_KEY_SAMPLE_INFO
    fid = response.feature_store_id
    o = r.hget(name=name, key=fid)
    if not o:
        logger.error(f"can't find {name}:{fid} in redis")
        return
    sample = QalibSample(**json.loads(o))
    sample.confirmed = True if response.code == 0 else False
    r.hset(name=name, key=fid, value=sample.model_dump_json())


def do_task_update_pipeline(response: HxdTaskResponse):
    logger.info("do task: update pipeline")
    # todo
    pass


def do_task_update_chat(response: HxdTaskResponse):
    logger.info("do task: update pipeline")
    # todo
    pass


async def sync_hxd_task_response() -> None:
    """
    sync huixiangdou task response from redis and do relative process
    :return: None
    """
    o = r.rpop(biz_const.RDS_KEY_HXD_TASK_RESPONSE)
    if not o:
        logger.debug(f"rpop from {biz_const.RDS_KEY_HXD_TASK_RESPONSE} is empty")
        return
    hxd_task_response = HxdTaskResponse(**json.loads(o))
    if not hxd_task_response:
        logger.error(f"deserializing huixiangdou task response failed, raw: {o}")
        return
    task_type = hxd_task_response.type
    if task_type == HxdTaskType.ADD_DOC:
        do_task_add_doc(hxd_task_response)
    elif task_type == HxdTaskType.UPDATE_SAMPLE:
        do_task_update_sample(hxd_task_response)
    elif task_type == HxdTaskType.UPDATE_PIPELINE:
        do_task_update_pipeline(hxd_task_response)
    elif task_type == HxdTaskType.CHAT:
        do_task_update_chat(hxd_task_response)
    else:
        logger.error(f"unrecognized task type: {task_type}")
    return


def allow_scheduler(task):
    lock = Lock(r, f"{biz_const.RDS_KEY_SCHEDULER}-{task}")
    if lock.acquire(blocking=False):
        logger.info(f"{biz_const.RDS_KEY_SCHEDULER}-{task} is locked")
        return True
    return False


def start_scheduler():
    if not scheduler.running:
        # ensure only one scheduler task is running
        if allow_scheduler("sync_hxd_task_response"):
            logger.info("start scheduler of sync_hxd_task_respone")
            scheduler.add_job(sync_hxd_task_response, IntervalTrigger(seconds=0.1))  # 100ms
        # more scheduler job can be added here
        scheduler.start()


def release_scheduler_lock(task) -> bool:
    key = f"{biz_const.RDS_KEY_SCHEDULER}-{task}"
    r.delete(key)
    return False if r.exists(key) else True


def stop_scheduler():
    task_1 = "sync_hxd_task_response"
    if release_scheduler_lock(task_1):
        logger.info(f"release scheduler lock of {task_1} successfully.")
    else:
        logger.error(f"release scheduler lock of {task_1} failed. you should delete this key from redis manually.")
