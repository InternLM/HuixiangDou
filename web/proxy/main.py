# Listen HuiXiangDou:Task queue
import json
import os
import pdb
import shutil
import time
import types
from datetime import datetime, timedelta
# implement time lru cache
from functools import lru_cache, partial, wraps

import pytoml
import redis
from BCEmbedding.tools.langchain import BCERerank
from config import feature_store_base_dir, redis_host, redis_port, redis_passwd
from feature_store import FeatureStore
from helper import ErrorCode, Queue, TaskCode, parse_json_str, ocr
from langchain.embeddings import HuggingFaceEmbeddings
from loguru import logger
from retriever import Retriever
from worker import Worker
from llm_server_hybrid import llm_serve
from multiprocessing import Process, Value


def callback_task_state(feature_store_id: str, code: int, _type: str,
                        state: str, files_state: dict={}):
    resp = Queue(name='TaskResponse')
    target = {
        'feature_store_id': feature_store_id,
        'code': code,
        'type': _type,
        'state': state,
        'files_state': files_state
    }
    logger.debug(target)
    resp.put(json.dumps(
        target,
        ensure_ascii=False,
    ))


class CacheRetriever:

    def __init__(self, config_path: str, max_len: int = 4):
        self.cache = dict()
        self.max_len = max_len
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)['feature_store']
            embedding_model_path = config['embedding_model_path']
            reranker_model_path = config['reranker_model_path']

        # load text2vec and rerank model
        logger.info('loading test2vec and rerank models')
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_path,
            model_kwargs={'device': 'cuda'},
            encode_kwargs={
                'batch_size': 1,
                'normalize_embeddings': True
            })
        self.embeddings.client = self.embeddings.client.half()
        reranker_args = {
            'model': reranker_model_path,
            'top_n': 3,
            'device': 'cuda',
            'use_fp16': True
        }
        self.reranker = BCERerank(**reranker_args)

    def get(self, fs_id: str):
        if fs_id in self.cache:
            self.cache[fs_id]['time'] = time.time()
            return self.cache[fs_id]['retriever']

        BASE = feature_store_base_dir()
        workdir = os.path.join(BASE, fs_id, 'workdir')
        configpath = os.path.join(BASE, fs_id, 'config.ini')
        if not os.path.exists(workdir) or not os.path.exists(configpath):
            return None, 'workdir or config.ini not exist'

        with open(configpath, encoding='utf8') as f:
            reject_throttle = pytoml.load(
                f)['feature_store']['reject_throttle']

        if len(self.cache) >= self.max_len:
            # drop the oldest one
            del_key = None
            min_time = time.time()
            for key, value in enumerate(self.cache):
                cur_time = value['time']
                if cur_time < min_time:
                    min_time = cur_time
                    del_key = key

            if del_key is not None:
                del_value = self.cache[del_key]
                self.cache.pop(del_key)
                del del_value['retriever']

        retriever = Retriever(embeddings=self.embeddings,
                              reranker=self.reranker,
                              work_dir=workdir,
                              reject_throttle=reject_throttle)
        self.cache[fs_id] = {'retriever': retriever, 'time': time.time()}
        return retriever

    def pop(self, fs_id: str):
        if fs_id not in self.cache:
            return
        del_value = self.cache[fs_id]
        self.cache.pop(fs_id)
        # manually free memory
        del del_value


def callback_chat_state(feature_store_id: str, query_id: str, code: int,
                        state: str, text: str, ref: list):
    que = Queue(name='ChatResponse')

    target = {
        'feature_store_id': feature_store_id,
        'query_id': query_id,
        'response': {
            'code': code,
            'state': state,
            'text': text,
            'references': ref
        }
    }
    logger.debug(target)
    que.put(json.dumps(target, ensure_ascii=False))


def format_history(history):
    """format [{sender, content}] to [[user1, bot1],[user2,bot2]..] style."""
    ret = []
    last_id = -1

    user = ''
    concat_text = ''
    for item in history:
        if last_id == -1:
            last_id = item.sender
            concat_text = item.content
            continue
        if last_id == item.sender:
            # 和上一个相同， concat
            concat_text += '\n'
            concat_text += item.content
            continue

        # 和上一个不同，把目前所有的 concat_text 加到 user 或 bot 部分
        if last_id == 0:
            # user message
            user = concat_text
        elif last_id == 1:
            # bot reply
            ret.append([user, concat_text])
            user = ''

        # 把当前的 assign 给 last
        last_id = item.sender
        concat_text = item.content

    # 最后一个元素，处理一下
    if last_id == 0:
        # user message
        ret.append([concat_text, ''])
        logger.warning('chat history should not ends with user')
    elif last_id == 1:
        # bot reply
        ret.append([user, concat_text])

    return ret


def chat_with_featue_store(cache: CacheRetriever,
                           payload: types.SimpleNamespace):
    # "payload": {
    #     "feature_store_id": "STRING",
    #     "query_id": "STRING",
    #     "content": "STRING",
    #     "images": ["STRING"],
    #     "history": [{
    #         "sender": Integer,
    #         "content": "STRING"
    #     }]
    # }

    fs_id = payload.feature_store_id
    query_id = payload.query_id

    chat_state = partial(callback_chat_state,
                         feature_store_id=fs_id,
                         query_id=query_id)

    retriever = cache.get(fs_id=fs_id)

    BASE = feature_store_base_dir()
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')
    db_reject = os.path.join(workdir, 'db_reject')
    db_response = os.path.join(workdir, 'db_response')

    if not os.path.exists(workdir) or not os.path.exists(configpath) or not os.path.exists(db_reject) or not os.path.exists(db_response):
        chat_state(code=ErrorCode.PARAMETER_ERROR.value, text='',state='知识库未建立或建立异常，此时不能 chat。', ref=[])
        return

    worker = Worker(work_dir=workdir, config_path=configpath)

    # TODO parse images

    image_texts = []
    for image in payload.images:
        text = ocr(image)
        if text is not None:
            image_texts.append(text)
    image_text = '\n'.join(image_texts)

    history = format_history(payload.history)
    error, response, references = worker.generate(query=image_text+payload.content,
                                                  history=history,
                                                  retriever=retriever,
                                                  groupname='')
    if error != ErrorCode.SUCCESS:
        chat_state(code=error.value,
                   state=error.describe(),
                   text=response,
                   ref=references)
        return
    chat_state(code=ErrorCode.SUCCESS.value,
               state=ErrorCode.SUCCESS.describe(),
               text=response,
               ref=references)


def build_feature_store(cache: CacheRetriever, payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "file_abs_base": "STRING",
    #     "path_list": ["STRING"]
    # }
    abs_base = payload.file_abs_base
    files = payload.file_list
    fs_id = payload.feature_store_id
    path_list = []
    for filename in files:
        path_list.append(os.path.join(abs_base, filename))

    BASE = feature_store_base_dir()
    # build dir and config.ini if not exist
    workdir = os.path.join(BASE, fs_id, 'workdir')
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    configpath = os.path.join(BASE, fs_id, 'config.ini')
    if not os.path.exists(configpath):
        template_file = 'config-template.ini'
        if not os.path.exists(template_file):
            raise Exception(f'{template_file} not exist')
        shutil.copy(template_file, configpath)

    with open(os.path.join(BASE, fs_id, 'desc'), 'w', encoding='utf8') as f:
        f.write(payload.name)

    fs = FeatureStore(config_path=configpath,
                      embeddings=cache.embeddings,
                      reranker=cache.reranker)
    task_state = partial(callback_task_state,
                         feature_store_id=fs_id,
                         _type=TaskCode.FS_ADD_DOC.value)

    # try:
    counter, state_map = fs.initialize(filepaths=path_list, work_dir=workdir)
    files_state = []
    for k,v in state_map.items():
        files_state.append({
            'file': k,
            'status': v['status'],
            'desc': v['desc']
        })
    success_cnt, fail_cnt, skip_cnt = counter
    if success_cnt == len(path_list):
        # success
        task_state(code=ErrorCode.SUCCESS.value,
                   state=ErrorCode.SUCCESS.describe(),
                   files_state=files_state)
    elif success_cnt == 0:
        task_state(code=ErrorCode.FAILED.value, state='无文件被处理', files_state=files_state)
    else:
        state = f'完成{success_cnt}个文件，跳过{skip_cnt}个，{fail_cnt}个处理异常。请确认文件格式。'
        task_state(code=ErrorCode.SUCCESS.value, state=state, files_state=files_state)

    # except Exception as e:
    #     logger.error(str(e))
    #     task_state(code=ErrorCode.FAILED.value, state=str(e))


def update_sample(cache: CacheRetriever, payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "positve_path": "STRING",
    #     "negative_path": "STRING",
    # }

    positive = payload.positive
    negative = payload.negative
    fs_id = payload.feature_store_id

    # check
    task_state = partial(callback_task_state,
                         feature_store_id=fs_id,
                         _type=TaskCode.FS_UPDATE_SAMPLE.value)

    if len(positive) < 1 or len(negative) < 1:
        task_state(code=ErrorCode.BAD_PARAMETER.value,
                   state='正例为空。请根据真实用户问题，填写正例；同时填写几句场景无关闲聊作负例')
        return

    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')

    db_reject = os.path.join(workdir, 'db_reject')
    db_response = os.path.join(workdir, 'db_response')

    if not os.path.exists(workdir) or not os.path.exists(configpath) or not os.path.exists(db_reject) or not os.path.exists(db_response):
        task_state(code=ErrorCode.INTERNAL_ERROR.value,
                   state='知识库未建立或中途异常，已自动反馈研发。请重新建立知识库。')
        return

    # try:

    retriever = cache.get(fs_id=fs_id)
    retriever.update_throttle(config_path=configpath,
                              work_dir=workdir,
                              good_questions=positive,
                              bad_questions=negative)
    del retriever
    task_state(code=ErrorCode.SUCCESS.value,
               state=ErrorCode.SUCCESS.describe())

    # except Exception as e:
    #     logger.error(str(e))
    #     task_state(code=ErrorCode.FAILED.value, state=str(e))


def update_pipeline(payload: types.SimpleNamespace):
    # "payload": {
    #     "name": "STRING",
    #     "feature_store_id": "STRING",
    #     "web_search_token": ""
    # }
    fs_id = payload.feature_store_id
    token = payload.web_search_token

    # check
    task_state = partial(callback_task_state,
                         feature_store_id=fs_id,
                         _type=TaskCode.FS_UPDATE_PIPELINE.value)

    BASE = feature_store_base_dir()
    fs_id = payload.feature_store_id
    workdir = os.path.join(BASE, fs_id, 'workdir')
    configpath = os.path.join(BASE, fs_id, 'config.ini')

    if not os.path.exists(workdir) or not os.path.exists(configpath):
        task_state(code=ErrorCode.INTERNAL_ERROR.value,
                   state='知识库未建立或中途异常，已自动反馈研发。请重新建立知识库。')
        return

    with open(configpath, encoding='utf8') as f:
        config = pytoml.load(f)
    config['web_search']['x_api_key'] = token
    with open(configpath, 'w', encoding='utf8') as f:
        pytoml.dump(config, f)
    task_state(code=ErrorCode.SUCCESS.value,
               state=ErrorCode.SUCCESS.describe())


def process():
    que = Queue(name='Task')
    fs_cache = CacheRetriever('config-template.ini')

    logger.info('start wait task queue..')
    while True:
        # try:
        msg, error = parse_json_str(que.get())
        logger.info(msg)
        if error is not None:
            raise error

        logger.debug(f'process {msg.type}')
        if msg.type == TaskCode.FS_ADD_DOC.value:
            callback_task_state(feature_store_id=msg.payload.feature_store_id,
                                code=ErrorCode.WORK_IN_PROGRESS.value,
                                _type=msg.type,
                                state=ErrorCode.WORK_IN_PROGRESS.describe())
            fs_cache.pop(msg.payload.feature_store_id)
            build_feature_store(fs_cache, msg.payload)
        elif msg.type == TaskCode.FS_UPDATE_SAMPLE.value:
            callback_task_state(feature_store_id=msg.payload.feature_store_id,
                                code=ErrorCode.WORK_IN_PROGRESS.value,
                                _type=msg.type,
                                state=ErrorCode.WORK_IN_PROGRESS.describe())
            fs_cache.pop(msg.payload.feature_store_id)
            update_sample(fs_cache, msg.payload)
        elif msg.type == TaskCode.FS_UPDATE_PIPELINE.value:
            update_pipeline(msg.payload)
        elif msg.type == TaskCode.CHAT.value:
            chat_with_featue_store(fs_cache, msg.payload)
        else:
            logger.warning(f'unknown type {msg.type}, supported type {[TaskCode.FS_ADD_DOC.value, TaskCode.FS_UPDATE_SAMPLE.value, TaskCode.FS_UPDATE_PIPELINE.value, TaskCode.CHAT.value]}')

        # except Exception as e:
        #     logger.error(str(e))


if __name__ == '__main__':
    # start hybrid server
    # server_ready = Value('i', 0)
    # server_process = Process(target=llm_serve,
    #                             args=('config-template.ini', server_ready))
    # server_process.daemon = True
    # server_process.start()
    # while True:
    #     if server_ready.value == 0:
    #         logger.info('waiting for server to be ready..')
    #         time.sleep(3)
    #     elif server_ready.value == 1:
    #         break
    #     else:
    #         logger.error('start local LLM server failed, quit.')
    #         raise Exception('local LLM path')
    logger.info('Hybrid LLM Server start.')
    process()
