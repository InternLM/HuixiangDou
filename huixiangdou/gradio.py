import argparse
import json
import os
import time
import pdb
from multiprocessing import Process, Value

import cv2
import gradio as gr
import pytoml
from loguru import logger

from huixiangdou.primitive import Query
from huixiangdou.service import ErrorCode, SerialPipeline, llm_serve, start_llm_server


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
        help='SerialPipeline configuration path. Default value is config.ini')
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

def predict(text, image):
    if image is not None:
        filename = 'image.png'
        image_path = os.path.join(args.work_dir, filename)
        cv2.imwrite(image_path, image)
    else:
        image_path = None

    assistant = SerialPipeline(work_dir=args.work_dir, config_path=args.config_path)
    query = Query(text, image_path)

    pipeline = {'step': []}
    debug = dict()
    for sess in assistant.generate(query=query, history=[], groupname=''):
        status = {
            "state":str(sess.code),
            "response": sess.response,
            "refs": sess.references
        }

        print(status)
        pipeline['step'].append(status)
        pipeline['debug'] = sess.debug

        json_str = json.dumps(pipeline, indent=2, ensure_ascii=False)
        yield json_str

if __name__ == '__main__':
    args = parse_args()

    # start service
    if args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=args.config_path)

    with gr.Blocks() as demo:
        with gr.Row():
            input_question = gr.TextArea(label='Input the question.')
            input_image = gr.Image(label='Upload Image.')
        with gr.Row():
            run_button = gr.Button()
        with gr.Row():
            result = gr.TextArea(label='HuixiangDou pipline status', show_copy_button=True)
        run_button.click(predict, [input_question, input_image], [result])

    demo.queue()
    demo.launch(share=False, server_name='0.0.0.0', debug=True)
