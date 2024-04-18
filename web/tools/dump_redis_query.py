import json
import os

from loguru import logger
from redis import Redis


def redis_host():
    host = os.getenv('REDIS_HOST')
    if host is None or len(host) < 1:
        raise Exception('REDIS_HOST not config')
    return host


def redis_port():
    port = os.getenv('REDIS_PORT')
    if port is None:
        logger.debug('REDIS_PORT not set, try 6379')
        port = 6379
    return port


def redis_passwd():
    passwd = os.getenv('REDIS_PASSWORD')
    if passwd is None or len(passwd) < 1:
        raise Exception('REDIS_PASSWORD not config')
    return passwd


def feature_store_base_dir():
    return 'feature_stores'

db = Redis(host=redis_host(),
           port=redis_port(),
           password=redis_passwd(),
           charset='utf-8',
           decode_responses=True)
keys = db.keys('HuixiangDou:query:*')

with open('query.jsonl', 'w') as f:
    for key in keys:
        value = db.hgetall(key)
        f.write(json.dumps(value, ensure_ascii=False))
        f.write('\n')
