from enum import Enum
from types import SimpleNamespace

import redis
from loguru import logger


class TaskCode(Enum):
    FS_ADD_DOC = 'add_doc'
    FS_UPDATE_SAMPLE = 'update_sample'
    CHAT = 'chat'
    CHAT_RESPONSE = 'chat_response'


class ErrorCode(Enum):
    """Define an enumerated type for error codes, each has a numeric value and
    a description.

    Each enum member is associated with a numeric code and a description
    string. The numeric code is used as the return code in function calls, and
    the description provides a human-readable explanation of the error.
    """
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

    WORK_IN_PROGRESS = 11, 'not finish'
    FAILED = 12, 'fail'
    BAD_PARAMETER = 13, 'bad parameter'
    INTERNAL_ERROR = 14, 'internal error'

    def __new__(cls, value, description):
        """Create new instance of ErrorCode."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __int__(self):
        """Return the integer representation of the error code."""
        return self.value

    def describe(self):
        """Return the description of the error code."""
        return self.description

    @classmethod
    def format(cls, code):
        """Format the error code into a JSON result.

        Args:
            code (ErrorCode): Error code to be formatted.

        Returns:
            dict: A dictionary that includes the error code and its description.  # noqa E501

        Raises:
            TypeError: If the input is not an instance of ErrorCode.
        """
        if isinstance(code, cls):
            return {'code': int(code), 'message': code.describe()}
        raise TypeError(f'Expected type {cls}, got {type(code)}')


class Queue:

    def __init__(self, name, namespace='HuiXiangDou', **redis_kwargs):
        self.__db = redis.Redis(**redis_kwargs)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def peek_tail(self):
        return self.__db.lrange(self.key, -1, -1)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.
        """
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            item = item[1]
        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)


def parse_json_str(json_str: str):
    try:
        return json.loads(json_str,
                          object_hook=lambda d: SimpleNamespace(**d)), None
    except Exception as e:
        logger.error(str(e))
        return None, e


class QueryTracker:
    """A class to track queries and log them into a file.

    This class provides functionality to keep track of queries and write them
    into a log file. Whenever a query is made, it can be logged using this
    class, and when the instance of this class is destroyed, all logged queries
    are written to the file.
    """

    def __init__(self, log_file_path):
        """Initialize the QueryTracker with the path of the log file."""
        self.log_file_path = log_file_path
        self.log_list = []

    def log(self, key, value=''):
        """Log a query.

        Args:
            key (str): The key associated with the query.
            value (str): The value or result associated with the query.
        """
        self.log_list.append((key, value))

    def __del__(self):
        """Write all logged queries into the file when the QueryTracker
        instance is destroyed.

        It opens the log file in append mode, writes all logged queries into
        the file, and then closes the file. If any exception occurs during this
        process, it will be caught and printed to standard output.
        """
        try:
            with open(self.log_file_path, 'a', encoding='utf8') as log_file:
                for key, value in self.log_list:
                    log_file.write(f'{key}: {value}\n')
                log_file.write('\n')
        except Exception as e:
            print(e)
