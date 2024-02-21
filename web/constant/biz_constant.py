import os
from web.util.log import log
logger = log(__name__)

# redis
RDS_KEY_LOGIN = "hxd::login::info"


# jwt
JWT_HEADER = {
    "alg": "HS256"
}
_jwt_secret = os.getenv("JWT_SECRET")
if not _jwt_secret:
    logger.error("Environment JWT_SECRET is None, you need set one, exiting with code 3")
    exit(3)
JWT_SECRET = _jwt_secret
