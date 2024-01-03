import argparse
from service import Worker, ErrorCode, llm_serve
from frontend import Lark
from loguru import logger
import pdb
import pytoml
import time
from multiprocessing import Process, Value


def parse_args():
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Worker configuration path. Default value is config.ini')
    parser.add_argument(
        '--standalone',
        action='store_true',
        default=False,
        help='Atuo deploy required Hybrid LLM Service.'
    )
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()

    if args.standalone:
        # hybrid llm serve
        server_ready = Value('b', False)
        server_process = Process(target=llm_serve, args=(args.config_path, server_ready))
        server_process.daemon = True
        server_process.start()
        while not server_ready.value:
            logger.info('waiting for server to be ready..')
            time.sleep(3)
        logger.info('Hybrid LLM Server start.')

    # query by worker
    with open(args.config_path) as f:
        fe_config = pytoml.load(f)['frontend']
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)
    # querys = ['请教下视频流检测 跳帧  造成框一闪一闪的  有好的优化办法吗', '请教各位佬一个问题，虽然说注意力的长度等于上下文的长度。但是，增大上下文推理长度难道只有加长注意力机制一种方法吗？比如Rope啥的，应该不是吧', '大佬们，现在要做一个轻量级的抬手放手检测，有什么好的模型吗？']
    querys = ['请教下视频流检测 跳帧  造成框一闪一闪的  有好的优化办法吗']

    for query in querys:
        code, reply = assistant.generate(query=query, history=[], groupname='')
        logger.info(f'{code}, {query}, {reply}')
        if fe_config['type'] == 'lark' and code == ErrorCode.SUCCESS:
            # send message to lark group
            lark = Lark(webhook=fe_config['webhook_url'])
            logger.info(f'send {reply} to lark group.')
            lark.send_text(msg=reply)

    # server_process.join()
