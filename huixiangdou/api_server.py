import argparse

from .services import SerialPipeline, ParallelPipeline
from .primitive import Query
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
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

    def event_stream():
        for sess in assistant.generate(query=query):
            status = {
                "state":str(sess.code),
                "response": sess.response,
                "refs": sess.references
            }

            pipeline['step'].append(status)
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
    parser = argparse.ArgumentParser(description='Serial or Parallel Pipeline.')
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
    parser.add_argument('--port', type=int, default=23333, help='Bind port, use 23333 by default.')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    # setup chat service
    if 'chat_with_repo' in args.pipeline:
        assistant = ParallelPipeline(work_dir=args.work_dir, config_path=args.config_path)
    elif 'chat_in_group' in args.pipeline:
        assistant = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)
    uvicorn.run(app, host='0.0.0.0', port=args.port, log_level='info')
