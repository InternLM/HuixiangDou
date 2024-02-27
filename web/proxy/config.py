import json
def redis_host():
    with open('redis.conf') as f:
        redis_conf = json.load(f)
    return redis_conf['host']

def redis_port():
    return 6379

def redis_passwd():
    with open('redis.conf') as f:
        redis_conf = json.load(f)
    return redis_conf['passwd']

def feature_store_base_dir():
    return 'feature_stores'
