from enum import Enum


class ErrorCode(Enum):
    SUCCESS = 0, "成功"
    NOT_A_QUESTION = 1, "query 不是一个疑问句"
    NO_TOPIC = 2, "问题找不到主题。可能是无意义的问句"
    UNRELATED = 3, "和底库无关的话题。更新 good_questions 和 bad_questions 可以提升准确度"
    NO_SEARCH_KEYWORDS = 4, "提取不出关键字"
    NO_SEARCH_RESULT = 5, "检索不出结果"
    BAD_ANSWER = 6, "答非所问"
    SECURITY = 7, "答复和违禁主题关联度太高"
    NOT_WORK_TIME = 8, "非工作时间。可修改 config.ini 调整。**在言论可能引发风险的场景，请让机器人保持在人类的监控下运行**"

    PARAMETER_ERROR = 9, "http 接口参数错误。query 不能为空； history 格式是 list of list，如 [['问题1','答复1'], ['问题2'], ['答复2']] "
    PARAMETER_MISS = 10, "http json 入参缺少 key"

    def __new__(cls, value, description):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __int__(self):
        return self.value

    def describe(self):
        return self.description

    @classmethod
    def format(cls, code):
        # 格式化错误码为 json 结果
        if isinstance(code, cls):
            return {'code': int(code), 'message': code.describe()}
        else:
            raise TypeError(f"Expected type {cls}, got {type(code)}")


class QueryTracker:

    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.log_list = []

    def log(self, key, value=''):
        self.log_list.append((key, value))

    def __del__(self):
        try:
            with open(self.log_file_path, 'a') as log_file:
                for key, value in self.log_list:
                    log_file.write(f'{key}: {value}\n')
                log_file.write('\n')
        except Exception as e:
            print(e)
