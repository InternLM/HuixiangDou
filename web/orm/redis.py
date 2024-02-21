import os
import redis
from web.util.log import log
logger = log(__name__)


logger.info("connecting to redis")
host = "localhost" if os.getenv("REDIS_HOST") is None else os.getenv("REDIS_HOST")
password = "default_password" if os.getenv("REDIS_PASSWORD") is None else os.getenv("REDIS_PASSWORD")
port = 6379 if os.getenv("REDIS_PORT") is None else os.getenv("REDIS_PORT")
db = 0 if os.getenv("REDIS_DB") is None else os.getenv("REDIS_DB")
pool = redis.ConnectionPool(host=host, port=port, db=db, password=password)
r = redis.Redis(connection_pool=pool)
try:
    r_res = r.ping()
    if not r_res:
        logger.error(f"Failed connected to redis, exit with code 1")
        exit(1)
except Exception as e:
    logger.error(f"Failed connected to redis, error={e}")
    exit(2)
logger.info("connected to redis")
