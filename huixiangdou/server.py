import argparse
import os
import time

import pytoml
import requests
from aiohttp import web
from loguru import logger
from termcolor import colored

from .service import ErrorCode, SerialPipeline, ParallelPipeline, start_llm_server
from .primitive import Query
import asyncio
from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
from typing import List

assistant = None
app = FastAPI(docs_url='/')

class Talk(BaseModel):
    text: str
    image: str = ''

def format_refs(refs: List[str]):
    refs_filter = list(set(refs))
    if len(refs) < 1:
        return ''

    text = '**References:**\r\n'
    for file_or_url in refs_filter:
        text += '* {}\r\n'.format(file_or_url)
    text += '\r\n'
    return text

@app.post("/huixiangdou_inference")
async def huixiangdou_inference(talk: Talk):
    global assistant
    query = Query(talk.text, talk.image)

    pipeline = {'step': []}
    debug = dict()
    if type(assistant) is SerialPipeline:
        for sess in assistant.generate(query=query):
            status = {
                "state":str(sess.code),
                "response": sess.response,
                "refs": sess.references
            }

            pipeline['step'].append(status)
            pipeline['debug'] = sess.debug
        return pipeline
        
    else:
        sentence = ''
        async for sess in assistant.generate(query=query, enable_web_search=False):
            if sentence == '' and len(sess.references) > 0:
                sentence = format_refs(sess.references)

            if len(sess.delta) > 0:
                sentence += sess.delta
        return sentence


@app.post("/huixiangdou_stream")
async def huixiangdou_stream(talk: Talk):
    global assistant
    query = Query(talk.text, talk.image)

    pipeline = {'step': []}
    debug = dict()

    def event_stream():
        for sess in assistant.generate(query=query):
            status = {
                "state":str(sess.code),
                "response": sess.response,
                "refs": sess.references
            }

            pipeline['step'].append(status)
            pipeline['debug'] = sess.debug
            yield json.dumps(pipeline)

    async def event_stream_async():
        sentence = ''
        async for sess in assistant.generate(query=query, enable_web_search=False):
            if sentence == '' and len(sess.references) > 0:
                sentence = format_refs(sess.references)

            if len(sess.delta) > 0:
                sentence += sess.delta
                yield sentence

    if type(assistant) is SerialPipeline:
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        return StreamingResponse(event_stream_async(), media_type="text/event-stream")

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='SerialPipeline.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Configuration path. Default value is config.ini')
    parser.add_argument('--pipeline', type=str, choices=['chat_with_repo', 'chat_in_group'], default='chat_with_repo', 
                        help='Select pipeline type for difference scenario, default value is `chat_with_repo`')
    parser.add_argument('--standalone',
                        action='store_true',
                        default=True,
                        help='Auto deploy required Hybrid LLM Service.')
    parser.add_argument('--no-standalone',
                        action='store_false',
                        dest='standalone',  # 指定与上面参数相同的目标
                        help='Do not auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    # start service
    if args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=main_args.config_path)
    # setup chat service
    if 'chat_with_repo' in args.pipeline:
        assistant = ParallelPipeline(work_dir=args.work_dir, config_path=args.config_path)
    elif 'chat_in_group' in args.pipeline:
        assistant = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)
    uvicorn.run(app, host='0.0.0.0', port=23333, log_level='info')
