import json

from web.util.log import log
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from web.orm.redis import r
import web.constant.biz_constant as biz_const
from web.model.huixiangdou import HxdTaskResponse, HxdTaskType
from redis.lock import Lock

logger = log(__name__)
scheduler = AsyncIOScheduler()


def do_task_add_doc():
    logger.info("do task: add doc")
    pass


def do_task_update_sample():
    logger.info("do task: update sample")

    pass


def do_task_update_pipeline():
    logger.info("do task: update pipeline")

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
        do_task_add_doc()
    elif task_type == HxdTaskType.UPDATE_SAMPLE:
        do_task_update_sample()
    elif task_type == HxdTaskType.UPDATE_PIPELINE:
        do_task_update_pipeline()
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
