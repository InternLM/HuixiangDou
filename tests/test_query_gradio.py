import argparse
import json
import time
from multiprocessing import Process, Value

import gradio as gr
import pytoml
from loguru import logger

from huixiangdou.service import ErrorCode, Worker, llm_serve, start_llm_server


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Worker configuration path. Default value is config.ini')
    parser.add_argument('--standalone',
                        action='store_true',
                        default=True,
                        help='Auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args


args = parse_args()


def get_reply(query):
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)
    code, reply, references = assistant.generate(query=query,
                                                 history=[],
                                                 groupname='')
    ret = dict()
    ret['text'] = str(reply)
    ret['code'] = int(code)
    ret['references'] = references

    return json.dumps(ret, indent=2, ensure_ascii=False)


# start service
if args.standalone is True:
    # hybrid llm serve
    start_llm_server(config_path=args.config_path)

with gr.Blocks() as demo:
    with gr.Row():
        input_question = gr.Textbox(label='输入你的提问')
        with gr.Column():
            result = gr.Textbox(label='生成结果')
            run_button = gr.Button()
    run_button.click(fn=get_reply, inputs=input_question, outputs=result)

demo.launch(share=False, server_name='0.0.0.0', debug=True)
