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

assistant = SerialPipeline(work_dir='workdir', config_path='config.ini')
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

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=23333, log_level='info')
