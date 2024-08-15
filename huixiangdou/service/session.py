from huixiangdou.primitive import Query
from .helper import ErrorCode
import os
import json

class Session:
    """For compute graph, `session` takes all parameter."""

    def __init__(self,
                 query: Query,
                 history: list,
                 groupname: str = '',
                 log_path: str = 'logs/generate.jsonl',
                 groupchats: list = []):
        self.stage = 'init'
        self.query = query
        self.history = history
        self.groupname = groupname
        self.groupchats = groupchats

        # init
        # Same as `chunk.choices[0].delta`
        self.delta = ''
        self.parallel_chunks = []
        self.response = ''
        self.references = []
        self.topic = ''
        self.code = ErrorCode.INIT

        # coreference resolution results
        self.cr = ''

        # text2vec results
        self.chunk = ''
        self.knowledge = ''

        # web search results
        self.web_knowledge = ''

        # source graph search results
        self.sg_knowledge = ''

        # debug logs
        self.debug = dict()
        self.log_path = log_path

    def __del__(self):
        dirname = os.path.dirname(self.log_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(self.log_path, 'a') as f:
            json_str = json.dumps(self.debug, indent=2, ensure_ascii=False)
            f.write(json_str)
            f.write('\n')
