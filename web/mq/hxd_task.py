import web.constant.biz_constant as biz_const
from web.model.huixiangdou import HxdTask, HxdTaskType
from web.orm.redis import r
from web.service.cache import ChatCache
from web.util.log import log

logger = log(__name__)


class HuixiangDouTask:

    def __init__(self):
        pass

    def updateTask(self, task: HxdTask) -> bool:
        """update task into redis.

        :param task: HxdTask
        :return: bool: True or False
        """
        if not task:
            logger.error("HuixiangDou's task is empty, update task aborted.")
            return False

        ChatCache.mark_monthly_active(task.payload.feature_store_id)
        if task.type == HxdTaskType.CHAT:
            ChatCache.add_inference_number()

        try:
            r.rpush(biz_const.RDS_KEY_HXD_TASK, task.model_dump_json())
        except Exception as e:
            logger.error(f'{e}')
            return False
        return True
