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

assistant = None
app = FastAPI(docs_url='/')

class Talk(BaseModel):
    text: str
    image: str = ''

@app.post("/huixiangdou_inference")
async def huixiangdou_inference(talk: Talk):
    global assistant
    query = Query(talk.text, talk.image)

    pipeline = {'step': []}
    debug = dict()
    for sess in assistant.generate(query=query, history=[], groupname=''):
        status = {
            "state":str(sess.code),
            "response": sess.response,
            "refs": sess.references
        }

        pipeline['step'].append(status)
        pipeline['debug'] = sess.debug

    return pipeline


@app.post("/huixiangdou_stream")
async def huixiangdou_stream(talk: Talk):
    global assistant
    query = Query(talk.text, talk.image)

    pipeline = {'step': []}
    debug = dict()

    def event_stream():
        for sess in assistant.generate(query=query, history=[], groupname=''):
            status = {
                "state":str(sess.code),
                "response": sess.response,
                "refs": sess.references
            }

            pipeline['step'].append(status)
            pipeline['debug'] = sess.debug
            yield json.dumps(pipeline)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

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
    parser.add_argument('--standalone',
                        action='store_true',
                        default=False,
                        help='Auto deploy required Hybrid LLM Service.')
    parser.add_argument('--pipeline', type=str, choices=['chat_with_repo', 'chat_in_group'], default='chat_with_repo', 
                        help='Select pipeline type for difference scenario, default value is `chat_with_repo`')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    if 'chat_with_repo' in args.pipeline:
        assistant = ParallelPipeline(work_dir=args.work_dir, config_path=args.config_path)
    elif 'chat_in_group' in args.pipeline:
        assistant = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)
    uvicorn.run(app, host='0.0.0.0', port=23333, log_level='info')
