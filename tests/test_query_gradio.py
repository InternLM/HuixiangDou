import argparse
import json
import os
import time
from multiprocessing import Process, Value

import cv2
import gradio as gr
import pytoml
from loguru import logger

from huixiangdou.primitive import Query
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


def get_reply(text, image):
    if image is not None:
        filename = 'image.png'
        image_path = os.path.join(args.work_dir, filename)
        cv2.imwrite(image_path, image)
    else:
        image_path = None

    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)
    query = Query(text, image_path)

    code, reply, references = assistant.generate(query=query,
                                                 history=[],
                                                 groupname='')
    ret = dict()
    ret['text'] = str(reply)
    ret['code'] = int(code)
    ret['references'] = references

    return json.dumps(ret, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    args = parse_args()

    # start service
    if args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=args.config_path)

    with gr.Blocks() as demo:
        with gr.Row():
            input_question = gr.Textbox(label='Input the question.')
            input_image = gr.Image(label='Upload Image.')
            with gr.Column():
                result = gr.Textbox(label='Generate response.')
                run_button = gr.Button()
        run_button.click(fn=get_reply,
                         inputs=[input_question, input_image],
                         outputs=result)

    demo.launch(share=False, server_name='0.0.0.0', debug=True)
