import argparse
from service import Worker
from service import ErrorCode
from frontend import Lark
from loguru import logger
import pdb
import pytoml

def parse_args():
    parser = argparse.ArgumentParser(description='Worker.')
    parser.add_argument('work_dir', type=str, help='Working directory.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Worker configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    with open(args.config_path) as f:
        fe_config = pytoml.load(f)['frontend']
    assistant = Worker(work_dir=args.work_dir, config_path=args.config_path)
    querys = ['请问如何安装 mmdeploy']

    for query in querys:
        code, reply = assistant.generate(query=query, history=[], groupname='')
        logger.info(f'{code}, {reply}')
        if fe_config['type'] == 'lark' and code == ErrorCode.SUCCESS:
            # send message to lark group
            lark = Lark(webhook=fe_config['webhook_url'])
            logger.info(f'send {reply} to lark group.')
            lark.send_text(msg=reply)
