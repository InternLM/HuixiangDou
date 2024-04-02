import redis

from web.config.env import HuixiangDouEnv
from web.util.log import log

logger = log(__name__)

logger.info('connecting to redis')
host = HuixiangDouEnv.get_redis_host()
password = HuixiangDouEnv.get_redis_password()
port = HuixiangDouEnv.get_redis_port()
db = HuixiangDouEnv.get_redis_db()
pool = redis.ConnectionPool(host=host, port=port, db=db, password=password)
r = redis.Redis(connection_pool=pool)
try:
    r_res = r.ping()
    if not r_res:
        logger.error(f'Failed connected to redis, exit with code 1')
        exit(1)
except Exception as e:
    logger.error(f'Failed connected to redis, error={e}')
    exit(2)
logger.info('connected to redis')
