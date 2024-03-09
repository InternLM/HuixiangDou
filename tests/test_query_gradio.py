import gradio as gr
import pytoml
from loguru import logger

from huixiangdou.frontend import Lark
from huixiangdou.service import ErrorCode, Worker


def build_reply_text(reply: str, references: list):
    if len(references) < 1:
        return reply

    ret = reply
    for ref in references:
        ret += '\n'
        ret += ref
    return ret


def lark_send_only(queries, assistant, fe_config: dict):
    logger.info(f'now queries: {queries}')
    for query in queries:
        code, reply, references = assistant.generate(query=query,
                                                     history=[],
                                                     groupname='')
        reply_text = build_reply_text(reply=reply, references=references)
        if fe_config['type'] == 'lark' and code == ErrorCode.SUCCESS:
            lark = Lark(webhook=fe_config['webhook_url'])
            logger.info(f'send {reply} and {references} to lark group.')
            lark.send_text(msg=reply_text)
    return reply


config_path = 'config.ini'
work_dir = 'workdir'

with open(config_path, encoding='utf8') as f:
    fe_config = pytoml.load(f)['frontend']
logger.info('Config loaded.')
assistant = Worker(work_dir=work_dir, config_path=config_path)
fe_type = fe_config['type']


def get_reply(input):
    return lark_send_only([input], assistant, fe_config)


with gr.Blocks() as demo:
    with gr.Row():
        input_question = gr.Textbox(label='输入你的提问')
        with gr.Column():
            result = gr.Textbox(label='生成结果')
            run_button = gr.Button(label='运行')
    run_button.click(fn=get_reply, inputs=input_question, outputs=result)

if __name__ == '__main__':
    # 取消 main.py 中的 server_process.join() 注释既可用该文件进行本地单元测试
    demo.launch(share=True)
