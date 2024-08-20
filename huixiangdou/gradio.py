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
from typing import List
from huixiangdou.primitive import Query
from huixiangdou.service import ErrorCode, SerialPipeline, ParallelPipeline, llm_serve, start_llm_server
import json

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

language='en'
enable_web_search=False
pipeline='chat_with_repo'
main_args = None
paralle_assistant = None
serial_assistant = None

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


def format_refs(refs: List[str]):
    refs_filter = list(set(refs))
    if len(refs) < 1:
        return ''
    text = ''
    if language == 'zh':
        text += '参考资料：\r\n'
    else:
        text += '**References:**\r\n'
    
    for file_or_url in refs_filter:
        text += '* {}\r\n'.format(file_or_url)
    text += '\r\n'
    return text


async def predict(text:str, image:str):
    global language
    global enable_web_search
    global pipeline
    global main_args
    global serial_assistant
    global paralle_assistant

    with open('query.txt', 'a') as f:
        f.write(json.dumps({'data': text}))
        f.write('\n')

    if image is not None:
        filename = 'image.png'
        image_path = os.path.join(args.work_dir, filename)
        cv2.imwrite(image_path, image)
    else:
        image_path = None

    query = Query(text, image_path)
    if 'chat_in_group' in pipeline:
        if serial_assistant is None:
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

    else:
        if paralle_assistant is None:
            paralle_assistant = ParallelPipeline(work_dir=main_args.work_dir, config_path=main_args.config_path)
        args = {'query':query, 'history':[], 'language':language}
        args['enable_web_search'] = enable_web_search

        sentence = ''
        async for sess in paralle_assistant.generate(**args):
            if sentence == '' and len(sess.references) > 0:
                sentence = format_refs(sess.references)

            if len(sess.delta) > 0:
                sentence += sess.delta
                yield sentence
        
        yield sentence

if __name__ == '__main__':
    main_args = parse_args()

    # start service
    if main_args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=main_args.config_path)

    with gr.Blocks(theme=gr.themes.Soft(), title='HuixiangDou AI assistant', analytics_enabled=True) as demo:
        with gr.Row():
            gr.Markdown("""
            #### [HuixiangDou](https://github.com/internlm/huixiangdou) AI assistant
            """, label='Reply', header_links=True, line_breaks=True,)
        with gr.Row():
            with gr.Column():
                ui_pipeline = gr.Radio(["chat_with_repo", "chat_in_group"], label="Pipeline type", info="Group-chat is slow but accurate and safe, default value is `chat_with_repo`")
                ui_pipeline.change(fn=on_pipeline_changed, inputs=ui_pipeline, outputs=[])
            with gr.Column():
                ui_language = gr.Radio(["en", "zh"], label="Language", info="Use `en` by default                                 ")
                ui_language.change(fn=on_language_changed, inputs=ui_language, outputs=[])
            with gr.Column():
                ui_web_search = gr.Radio(["no", "yes"], label="Enable web search", info="Disable by default                                 ")
                ui_web_search.change(on_web_search_changed, inputs=ui_web_search, outputs=[])

        with gr.Row():
            input_question = gr.TextArea(label='Input your question', placeholder='how to install mmpose ?', show_copy_button=True, lines=9)
            input_image = gr.Image(label='[Optional] Image-text retrieval needs `config-multimodal.ini`')
        with gr.Row():
            run_button = gr.Button()
        with gr.Row():
            result = gr.Markdown('>Text reply or inner status callback here, depends on `pipeline type`', label='Reply', show_label=True, header_links=True, line_breaks=True, show_copy_button=True)
            # result = gr.TextArea(label='Reply', show_copy_button=True, placeholder='Text Reply or inner status callback, depends on `pipeline type`')
            
        run_button.click(predict, [input_question, input_image], [result])
    demo.queue()
    demo.launch(share=False, server_name='0.0.0.0', debug=True)
