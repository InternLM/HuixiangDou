from llm_client import ChatClient
import os
import ast
import json
import pdb
import argparse
from loguru import logger
import pytoml

class SourceGraphProxy:
    def __init__(self, config_path: dict, topk=1) -> None:
        self.config_path = config_path
        self.topk = topk

    def command(self, txt: str):
        logger.debug('cmd: {}'.format(txt))
        cmd = os.popen(txt)
        return cmd.read().rstrip().lstrip()

    def load_config(self):
        with open(self.config_path) as f:
            config = pytoml.load(f)
            sg_config = config['sg_search']
        
        bin_path = sg_config['binary_src_path']
        if bin_path is None or not os.path.exists(bin_path):
            raise Exception(f'sg_search enabled while binary_src_path {bin_path} not exist')

        token = sg_config['src_access_token']
        if token is None or token == 'YOUR-ACCESS-TOKEN':
            raise Exception(f'sg_search enabled while sr_access_token {bin_path} not exist')
        return sg_config

    def extract_sg_result(self, jsonstr):
        ret = []
        try:
            root = json.loads(jsonstr)
            results = root['Results']
            for result in results:
                if 'FileMatch' != result['__typename']:
                    continue

                content = result['file']['content']
                path = result['file']['path']
                ret.append({'filepath':path, 'content':content})

                if len(ret) >= self.topk:
                    break
        except Exception as e:
            logger.warning('{} when source graph parse {}'.format(str(e), jsonstr))
        return ret

    def search(self, llm, question, groupname):
        # write your own open source repo here !
        prompt = '''你是 {} 技术群的技术助手，目前收到了用户的问题：“{}”。请问这个问题应该查询以下哪个开源项目：
* lmdeploy。lmdeploy 是一个用于压缩、部署和服务 LLM（Large Language Model）的工具包。是一个服务端场景下，transformer 结构 LLM 部署工具，支持 GPU 服务端部署，速度有保障，支持 Tensor Parallel，多并发优化，功能全面，包括模型转换、缓存历史会话的 cache feature 等. 它还提供了 WebUI、命令行和 gRPC 客户端接入。
* xtuner。xtuner 是一个用于调优大型语言模型（LLM）的工具箱。
* opencompass。用于评测大型语言模型（LLM）. 它提供了完整的开源可复现的评测框架，支持大语言模型、多模态模型的一站式评测，基于分布式技术，对大参数量模型亦能实现高效评测。评测方向汇总为知识、语言、理解、推理、考试五大能力维度，整合集纳了超过70个评测数据集，合计提供了超过40万个模型评测问题，并提供长文本、安全、代码3类大模型特色技术能力评测。
* 不知道。
请直接告诉我项目名称不要解释，如果都不是就回答不知道。'''.format(question, groupname)

        choice = llm.generate_response(prompt=prompt, remote=False).lower().strip()
        REPO = ''
        if 'lmdeploy' in choice:
            REPO = 'internlm/lmdeploy'
        elif 'opencompass' in choice:
            REPO = 'open-compass/opencompass'
        elif 'xtuner' in choice:
            REPO = 'internlm/xtuner'
        else:
            return ''

        sg_config = self.load_config()
        ENV = 'export SRC_ACCESS_TOKEN="{}" && '.format(sg_config['src_access_token'])
        BINARY = sg_config['binary_src_path']

        prompt = '“{}”\n请仔细阅读以上问题，提取其中可用作搜索引擎的关键字，关键字直接用 list 表示，不要解释。'.format(question)
        entities = []
        try:
            entity_str = llm.generate_response(prompt=prompt)
            entities = ast.literal_eval(entity_str)
        except Exception as e:
            logger.error('parse {} failed {}.'.format(entity_str, str(e)))
            return ''
        search_items = []
        for entity in entities:
            # 根据实体词，搜文档和源码
            # search -json 'repo:open-compass/opencompass  summarizers'
            cmd_doc = '''{} search -json 'repo:{} lang:MarkDown {}' '''.format(BINARY, REPO, entity)
            cmd_return = self.command(ENV + cmd_doc)
            search_items += self.extract_sg_result(cmd_return)

            cmd_python = '''{} search -json 'repo:{} lang:Python {}' '''.format(BINARY, REPO, entity)
            cmd_return = self.command(ENV + cmd_python)
            search_items += self.extract_sg_result(cmd_return)

        search_text = json.dumps(search_items, ensure_ascii=False, indent=2)
        return search_text

def parse_args():
    parser = argparse.ArgumentParser(description='Source graph proxy search')
    parser.add_argument('--config_path', default='config.ini',
                        help='Source graph proxy configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    logger.add('logs/sg_search.log', rotation="4MB")
    args = parse_args()

    llm = ChatClient(config_path=args.config_path)
    sg = SourceGraphProxy(config_path=args.config_path)
    context = sg.search(llm, question='请问triviaqa 5shot结果怎么在summarizer里输出呢', groupname='opencompass')
    print(context)
