import os
from web.util.log import log

logger = log(__name__)

# redis
RDS_KEY_LOGIN = "HuixiangDou:login:info"
RDS_KEY_QALIB_INFO = "HuixiangDou:qalib:info"
RDS_KEY_SAMPLE_INFO = "HuixiangDou:qalib:sample"
RDS_KEY_HXD_TASK = "HuixiangDou:Task"
RDS_KEY_HXD_TASK_RESPONSE = "HuixiangDou:TaskResponse"
RDS_KEY_SCHEDULER = "HuixiangDou:sched"

# jwt
JWT_HEADER = {
    "alg": "HS256"
}
_jwt_secret = os.getenv("JWT_SECRET")
if not _jwt_secret:
    logger.error("Environment JWT_SECRET is None, you need set one, exiting with code 3")
    exit(3)
JWT_SECRET = _jwt_secret

# cookie
HXD_COOKIE_KEY = "hxd_token"

# error codes
ERR_QALIB_API_NO_ACCESS = {
    "code": "A1000",
    "msg": "No access to this api"
}
ERR_ACCESS_CREATE = {
    "code": "A2000",
    "msg": "Create QA lib failed"
}
ERR_ACCESS_LOGIN = {
    "code": "A2001",
    "msg": "QA lib's name already exists or password does not match"
}
ERR_QALIB_INFO_NOT_FOUND = {
    "code": "A2002",
    "msg": "QA lib's info is not found"
}

# biz
HXD_QALIB_STATUS_INIT = 0
HXD_QALIB_STATUS_CREATED = 1
