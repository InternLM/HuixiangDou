import os

from web.util.log import log

logger = log(__name__)

# redis
RDS_KEY_LOGIN = "HuixiangDou:login:info"
RDS_KEY_QALIB_INFO = "HuixiangDou:qalib:info"
RDS_KEY_SUFFIX_TO_QALIB = "HuixiangDou:suffixMap"
RDS_KEY_SAMPLE_INFO = "HuixiangDou:qalib:sample"
RDS_KEY_PIPELINE = "HuixiangDou:pipeline"
RDS_KEY_HXD_TASK = "HuixiangDou:Task"
RDS_KEY_HXD_TASK_RESPONSE = "HuixiangDou:TaskResponse"
RDS_KEY_HXD_CHAT_RESPONSE = "HuixiangDou:ChatResponse"
RDS_KEY_SCHEDULER = "HuixiangDou:sched"
RDS_KEY_QUERY_INFO = "HuixiangDou:query"

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
ERR_CHAT = {
    "code": "A3001",
    "msg": "chat error"
}
ERR_NOT_EXIST_CHAT = {
    "code": "A3002",
    "msg": "query not exist"
}
ERR_INFO_UPDATE_FAILED = {
    "code": "A3003",
    "msg": "info update failed"
}
CHAT_STILL_IN_QUEUE = {
    "code": "A3100",
    "msg": "chat processing"
}


# biz
HXD_QALIB_STATUS_INIT = 0
HXD_QALIB_STATUS_CREATED = 1
# 1 day
HXD_CHAT_TTL = 86400

