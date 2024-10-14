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
from datetime import datetime

def ymd():
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    if not os.path.exists(date_string):
        os.makedirs(date_string)
    return date_string

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Gradio UI for parallel/serial pipeline.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
                        help='Working directory.')
    parser.add_argument('--pipeline-count', type=int, default=2, help='Support user choosing all pipeline types.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        type=str,
        help='Pipeline configuration path. Default value is config.ini')
    parser.add_argument('--standalone',
                        action='store_true',
                        default=True,
                        help='Auto deploy required Hybrid LLM Service.')
    parser.add_argument('--no-standalone',
                        action='store_false',
                        dest='standalone', 
                        help='Do not auto deploy required Hybrid LLM Service.')
    parser.add_argument('--placeholder', type=str, default='How to install HuixiangDou ?', help='Placeholder for user query.')
    parser.add_argument('--image', action='store_true', default=True, help='')
    parser.add_argument('--no-image', action='store_false', dest='image', help='Close some components for readthedocs.')
    parser.add_argument('--theme', type=str, default='soft', help='Gradio theme, default value is `soft`. Open https://www.gradio.app/guides/theming-guide for all themes.')

    args = parser.parse_args()
    return args

language='en'
enable_web_search=False
enable_code_search=True
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

def on_code_search_changed(value: str):
    global enable_code_search
    print(value)
    if 'no' in value:
        enable_code_search = False
    else:
        enable_code_search = True

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
        f.write(json.dumps({'data': text, 'date': ymd()}, ensure_ascii=False))
        f.write('\n')

    if image is not None:
        filename = 'image.png'
        image_path = os.path.join(main_args.work_dir, filename)
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
        args['enable_code_search'] = enable_code_search

        sentence = ''
        async for sess in paralle_assistant.generate(**args):
            if sentence == '' and len(sess.references) > 0:
                sentence = format_refs(sess.references)

            if len(sess.delta) > 0:
                sentence += sess.delta
                yield sentence
        
        yield sentence

def download_and_unzip(main_args):
    zip_filepath = os.path.join(main_args.feature_local, 'workdir.zip')
    main_args.work_dir = os.path.join(main_args.feature_local, 'workdir')
    logger.info(f'assign {main_args.work_dir} to args.work_dir')

    download_cmd = f'wget -O {zip_filepath} {main_args.feature_url}'
    os.system(download_cmd)

    if not os.path.exists(zip_filepath):
        raise Exception(f'zip filepath {zip_filepath} not exist.')

    unzip_cmd = f'unzip -o {zip_filepath} -d {main_args.feature_local}'
    os.system(unzip_cmd)
    if not os.path.exists(main_args.work_dir):
        raise Exception(f'feature dir {zip_dir} not exist.')

def build_feature_store(main_args):
    if os.path.exists('workdir'):
        logger.warning('feature_store `workdir` already exist, skip')
        return
    logger.info('start build feature_store..')
    os.system('python3 -m huixiangdou.service.feature_store --config_path {}'.format(main_args.config_path))

if __name__ == '__main__':
    main_args = parse_args()
    build_feature_store(main_args)

    show_image = True
    radio_options = ["chat_with_repo"]

    if not main_args.image:
        show_image = False

    if main_args.pipeline_count > 1:
        radio_options.append('chat_in_group')
    
    # start service
    if main_args.standalone is True:
        # hybrid llm serve
        start_llm_server(config_path=main_args.config_path)

    themes = {
        'soft': gr.themes.Soft(),
        'monochrome': gr.themes.Monochrome(),
        'base': gr.themes.Base(),
        'default': gr.themes.Default(),
        'glass': gr.themes.Glass()
    }
    if main_args.theme in themes:
        theme = themes[main_args.theme]
    else:
        theme = gr.themes.Soft()

    with gr.Blocks(theme=theme, title='HuixiangDou AI assistant', analytics_enabled=True) as demo:
        with gr.Row():
            gr.Markdown("""
            #### [HuixiangDou](https://github.com/internlm/huixiangdou) AI assistant
            """, label='Reply', header_links=True, line_breaks=True,)

        with gr.Row():
            if len(radio_options) > 1:
                with gr.Column():
                    ui_pipeline = gr.Radio(radio_options, label="Pipeline type", info="Group-chat is slow but accurate and safe, default value is `chat_with_repo`")
                    ui_pipeline.change(fn=on_pipeline_changed, inputs=ui_pipeline, outputs=[])
            with gr.Column():
                ui_language = gr.Radio(["en", "zh"], label="Language", info="Use `en` by default                                 ")
                ui_language.change(fn=on_language_changed, inputs=ui_language, outputs=[])
            with gr.Column():
                ui_web_search = gr.Radio(["no", "yes"], label="Enable web search", info="Disable by default                                 ")
                ui_web_search.change(fn=on_web_search_changed, inputs=ui_web_search, outputs=[])
            with gr.Column():
                ui_code_search = gr.Radio(["yes", "no"], label="Enable code search", info="Enable by default                                 ")
                ui_code_search.change(fn=on_code_search_changed, inputs=ui_code_search, outputs=[])

        with gr.Row():
            input_question = gr.TextArea(label='Input your question', placeholder=main_args.placeholder, show_copy_button=True, lines=9)
            input_image = gr.Image(label='[Optional] Image-text retrieval needs `config-multimodal.ini`', render=show_image)

        with gr.Row():
            run_button = gr.Button()

        with gr.Row():
            result = gr.Markdown('>Text reply or inner status callback here, depends on `pipeline type`', label='Reply', show_label=True, header_links=True, line_breaks=True, show_copy_button=True)
            # result = gr.TextArea(label='Reply', show_copy_button=True, placeholder='Text Reply or inner status callback, depends on `pipeline type`')

        run_button.click(predict, [input_question, input_image], [result])
    demo.queue()
    demo.launch(share=False, server_name='0.0.0.0', debug=True)
