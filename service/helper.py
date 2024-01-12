# Copyright (c) OpenMMLab. All rights reserved.
from enum import Enum


class ErrorCode(Enum):
    SUCCESS = 0, 'success'
    NOT_A_QUESTION = 1, 'query is not a question'
    NO_TOPIC = 2, 'The question does not have a topic. It might be a meaningless sentence.'  # noqa E501
    UNRELATED = 3, 'Topics unrelated to the knowledge base. Updating good_questions and bad_questions can improve accuracy.'  # noqa E501
    NO_SEARCH_KEYWORDS = 4, 'Cannot extract keywords.'
    NO_SEARCH_RESULT = 5, 'Cannot retrieve results.'
    BAD_ANSWER = 6, 'Irrelevant answer.'
    SECURITY = 7, 'Reply has a high relevance to prohibited topics.'
    NOT_WORK_TIME = 8, 'Non-working hours. The config.ini file can be modified to adjust this. **In scenarios where speech may pose risks, let the robot operate under human supervision**'  # noqa E501

    PARAMETER_ERROR = 9, "HTTP interface parameter error. Query cannot be empty; the format of history is list of lists, like [['question1', 'reply1'], ['question2'], ['reply2']]"  # noqa E501
    PARAMETER_MISS = 10, 'Missing key in http json input parameters.'

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
            raise TypeError(f'Expected type {cls}, got {type(code)}')


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
