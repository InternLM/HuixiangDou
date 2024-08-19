import argparse
import json
import os
import time
import pdb
from multiprocessing import Process, Value
import asyncio
import cv2
import gradio as gr
import pytoml
from loguru import logger

from huixiangdou.primitive import Query
from huixiangdou.service import ErrorCode, SerialPipeline, ParallelPipeline, llm_serve, start_llm_server


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
                        default=False,
                        help='Auto deploy required Hybrid LLM Service.')
    parser.add_argument('--no-standalone',
                        action='store_false',
                        dest='standalone',  # 指定与上面参数相同的目标
                        help='Do not auto deploy required Hybrid LLM Service.')
    args = parser.parse_args()
    return args

language='zh'
enable_web_search=True
pipeline='parallel'
main_args = None

def on_language_changed(value:str):
    global language
    print(value)
    language = value

def on_pipeline_changed(value:str):
    global pipeline
    print(value)
    pipeline = value

def on_web_search_changed(value: str):
    global enable_web_search
    print(value)
    if 'no' in value:
        enable_web_search = False
    else:
        enable_web_search = True

async def predict(text:str, image:str):
    global language
    global enable_web_search
    global pipeline
    global main_args

    if image is not None:
        filename = 'image.png'
        image_path = os.path.join(args.work_dir, filename)
        cv2.imwrite(image_path, image)
    else:
        image_path = None

    query = Query(text, image_path)
    if 'serial' in pipeline:
        serial_assistant = SerialPipeline(work_dir=main_args.work_dir, config_path=main_args.config_path)
        args = {'query':query, 'history': [], 'groupname':''}
        pipeline = {'status': {}}
        debug = dict()
        stream_chat_content = ''
        for sess in serial_assistant.generate(**args):
            if len(sess.delta) > 0:
                # start chat, display
                stream_chat_content += sess.delta
                yield stream_chat_content
            else:
                status = {
                    "state":str(sess.code),
                    "response": sess.response,
                    "refs": sess.references
                }
                pipeline['status'] = status
                pipeline['debug'] = sess.debug

                json_str = json.dumps(pipeline, indent=2, ensure_ascii=False)
                yield json_str
        del serial_assistant
    else:
        paralle_assistant = ParallelPipeline(work_dir=main_args.work_dir, config_path=main_args.config_path)
        args = {'query':query, 'history':[], 'language':language}
        args['enable_web_search'] = enable_web_search

        sentence = ''
        async for sess in paralle_assistant.generate(**args):
            if len(sess.delta) > 0:
                sentence += sess.delta
                yield sentence
        
        sentence += str(sess.references)
        yield sentence
        del paralle_assistant

if __name__ == '__main__':
    main_args = parse_args()

    # start service
    if main_args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=main_args.config_path)

    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                ui_language = gr.Radio(["zh", "en"], label="Language", info="Use zh_cn by default.")
                ui_language.change(fn=on_language_changed, inputs=ui_language, outputs=[])
            with gr.Column():
                ui_pipeline = gr.Radio(["parallel", "serial"], label="Pipeline type", info="Serial pipeline is slower but accurate, default value is `serial`")
                ui_pipeline.change(fn=on_pipeline_changed, inputs=ui_pipeline, outputs=[])
            with gr.Column():
                ui_web_search = gr.Radio(["yes", "no"], label="Enable web search", info="Enable web search")
                ui_web_search.change(on_web_search_changed, inputs=ui_web_search, outputs=[])

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
