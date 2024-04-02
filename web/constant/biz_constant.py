import os

from web.util.log import log

logger = log(__name__)

# redis
RDS_KEY_LOGIN = 'HuixiangDou:login:info'
RDS_KEY_QALIB_INFO = 'HuixiangDou:qalib:info'
RDS_KEY_SUFFIX_TO_QALIB = 'HuixiangDou:suffixMap'
RDS_KEY_SAMPLE_INFO = 'HuixiangDou:qalib:sample'
RDS_KEY_PIPELINE = 'HuixiangDou:pipeline'
RDS_KEY_HXD_TASK = 'HuixiangDou:Task'
RDS_KEY_HXD_TASK_RESPONSE = 'HuixiangDou:TaskResponse'
RDS_KEY_HXD_CHAT_RESPONSE = 'HuixiangDou:ChatResponse'
RDS_KEY_SCHEDULER = 'HuixiangDou:sched'
RDS_KEY_QUERY_INFO = 'HuixiangDou:query'
RDS_KEY_FEEDBACK_CASE = 'HuixiangDou:feedback:case'
RDS_KEY_LARK_CONFIG = 'HuixiangDou:lark'
RDS_KEY_QUERY_ID_TO_FETCH = 'HuixiangDou:queryIdToFetch'
RDS_KEY_AGENT_LARK_USED = 'HuixiangDou:agentLarkUsed'
RDS_KEY_AGENT_WECHAT_USED = 'HuixiangDou:agentWechatUsed'
RDS_KEY_QALIB_ACTIVE = 'HuixiangDou:monthlyActive'
RDS_KEY_TOTAL_INFERENCE_NUMBER = 'HuixiangDou:inference'
RDS_KEY_USER_INFERENCE = 'HuixiangDou:userInference'

# jwt
JWT_HEADER = {'alg': 'HS256'}

# cookie
HXD_COOKIE_KEY = 'hxd_token'

# error codes
ERR_QALIB_API_NO_ACCESS = {'code': 'A1000', 'msg': 'No access to this api'}
ERR_ACCESS_CREATE = {'code': 'A2000', 'msg': 'Create QA lib failed'}
ERR_ACCESS_LOGIN = {
    'code': 'A2001',
    'msg': "QA lib's name already exists or password does not match"
}
ERR_QALIB_INFO_NOT_FOUND = {
    'code': 'A2002',
    'msg': "QA lib's info is not found"
}
ERR_QALIB_ADD_DOCS_ONCE_MAX = {
    'code': 'A2003',
    'msg': "Exceeded the maximum total files' size for single adding docs"
}
ERR_CHAT = {'code': 'A3001', 'msg': 'Chat error'}
ERR_NOT_EXIST_CHAT = {'code': 'A3002', 'msg': 'Query not exist'}
ERR_INFO_UPDATE_FAILED = {'code': 'A3003', 'msg': 'Info update failed'}
ERR_CHAT_CASE_FEEDBACK = {'code': 'A3004', 'msg': 'Case feedback failed'}
CHAT_STILL_IN_QUEUE = {'code': 'A3100', 'msg': 'Chat processing'}

# biz
HXD_QALIB_STATUS_INIT = 0
HXD_QALIB_STATUS_CREATED = 1
HXD_PIPELINE_QALIB_CREATE_SUCCESS = 1
HXD_PIPELINE_QALIB_CREATE_FAILED = -1

# 1 day
HXD_CHAT_TTL = 86400

# 1000 MB
HXD_ADD_DOCS_ONCE_MAX = 1048576000

HXD_FEATURE_STORE_SUFFIX_LENGTH = 4
