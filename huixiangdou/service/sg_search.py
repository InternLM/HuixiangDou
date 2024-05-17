# Copyright (c) OpenMMLab. All rights reserved.
"""Search enhancement proxy."""
import argparse
import json
import os

import pytoml
from loguru import logger

from .llm_client import ChatClient


class SourceGraphProxy:
    """A class to serve as a proxy for interacting with the Source Graph.

    Args:
        config_path (str): Path to the configuration file.
        topk (int, optional): Top K results to consider from the search. Defaults to 1.  # noqa E501
        language (str, optional): Language for the system prompts - 'zh' for Chinese and 'en' for English. Defaults to 'zh'.  # noqa E501

    Attributes:
        config_path (str): The path of the configuration file.
        sg_config (dict): Configuration settings for sourcegraph search.
        topk (int): Top K results to consider from the search.
        language (str): Language for the system prompts.
        CHOICE_TEMPLATE (str): Template string for generating choice based on selected language.  # noqa E501
        KEYWORDS_TEMPLATE (str): Template string for generating keywords based on selected language.  # noqa E501
    """

    def __init__(self, config_path: str, topk=1, language: str = 'zh') -> None:
        """Init searcher with config."""
        self.config_path = config_path
        self.sg_config = None
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.sg_config = config['sg_search']

        self.topk = topk
        self.language = language
        if self.language == 'zh':
            self.CHOICE_TEMPLATE = '“{}”\n请仔细阅读以上问题，请问应该查询以下哪个开源项目：\n'  # noqa E501
            self.KEYWORDS_TEMPLATE = '“{}”\n请仔细阅读以上问题，提取其中可用作搜索引擎的关键字，关键字之间,分隔，不要解释。'  # noqa E501
        else:
            self.CHOICE_TEMPLATE = '"{}"\nPlease read the above question carefully, which of the following open-source projects should this question refer to: \n'  # noqa E501
            self.KEYWORDS_TEMPLATE = '"{}"\nPlease read the above questions carefully, extract the keywords which can be used as search engines, between keywords, separate, do not explain.'  # noqa E501

    def command(self, txt: str):
        """Executes a shell command and returns its output.

        Args:
            txt (str): Command to be executed in the shell.

        Returns:
            str: Output of the shell command execution.
        """
        logger.debug('cmd: {}'.format(txt))
        cmd = os.popen(txt)
        return cmd.read().rstrip().lstrip()

    def extract_sg_result(self, jsonstr):
        """Extracts the desired data from the source graph result.

        Args:
            jsonstr (str): JSON string containing source graph search result.

        Returns:
            list: List of dictionaries each contains 'filepath' and 'content' of the files returned by source graph.  # noqa E501
        """
        ret = []
        try:
            root = json.loads(jsonstr)
            results = root['Results']
            for result in results:
                if 'FileMatch' != result['__typename']:
                    continue

                content = result['file']['content']
                path = result['file']['path']
                ret.append({'filepath': path, 'content': content})

                if len(ret) >= self.topk:
                    break
        except Exception as e:
            logger.warning('{} when source graph parse {}'.format(
                str(e), jsonstr))
        return ret

    def choose_repo(self, llm_client, question, groupname):
        """Interactively assists user to select a repository for search based
        on user's question.

        Args:
            llm_client: Client instance for LLM.
            question (str): User's question.
            groupname (str): Name of the user's group.

        Returns:
            str: The ID of selected repository.
        """
        prompt = self.CHOICE_TEMPLATE.format(question)

        keys = self.sg_config.keys()
        skip = ['binary_src_path', 'src_access_token']
        repos = {}
        for key in keys:
            if key in skip:
                continue
            introduction = self.sg_config[key]['introduction']
            prompt += f'* {key} {introduction}\n'
            repos[key] = self.sg_config[key]
        prompt += '* none '
        choice = llm_client.generate_response(prompt=prompt,
                                              backend='remote').strip()

        target_repo_id = None
        for key in repos.keys():
            if key in choice:
                target_repo_id = repos[key]['github_repo_id']
                break

        return target_repo_id

    def search(self, llm_client, question, groupname):
        """Performs a search operation in the selected repository based on the
        user's question.

        Args:
            llm_client: Client instance for LLM.
            question (str): User's question.
            groupname (str): Name of the user's group.

        Returns:
            str: Search result from source graph in JSON format.
        """
        repo_id = self.choose_repo(llm_client, question, groupname)
        if repo_id is None:
            logger.warning('cannot choose repo_id')
            return ''

        ENV = 'export SRC_ACCESS_TOKEN="{}" && '.format(
            self.sg_config['src_access_token'])
        BINARY = self.sg_config['binary_src_path']
        if not os.path.exists(BINARY):
            raise Exception('{} not exist'.format(BINARY))
            return ''

        prompt = self.KEYWORDS_TEMPLATE.format(question)
        entities = []
        entity_str = ''
        try:
            entity_str = llm_client.generate_response(prompt=prompt)
            separator = ','
            if '，' in entity_str:
                separator = '，'
            entities = [
                item for item in entity_str.split(separator) if item.strip()
            ]
        except Exception as e:
            logger.error('parse {} failed {}.'.format(entity_str, str(e)))
            # return ''
            entities = []

        search_items = []
        for entity in entities:
            # search doc and source code based on entities
            # search -json 'repo:open-compass/opencompass  summarizers'
            cmd_doc = '''{} search -json 'repo:{} lang:MarkDown {}' '''.format(
                BINARY, repo_id, entity)
            cmd_return = self.command(ENV + cmd_doc)
            search_items += self.extract_sg_result(cmd_return)

            cmd_python = '''{} search -json 'repo:{} lang:Python {}' '''.format(  # noqa E501
                BINARY, repo_id, entity)
            cmd_return = self.command(ENV + cmd_python)
            search_items += self.extract_sg_result(cmd_return)

        search_text = json.dumps(search_items, ensure_ascii=False, indent=2)
        return search_text


def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description='Source graph proxy search')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help=  # noqa E251
        'Source graph proxy configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    """Test search."""
    logger.add('logs/sg_search.log', rotation='4MB')
    args = parse_args()

    llm = ChatClient(config_path=args.config_path)
    sg = SourceGraphProxy(config_path=args.config_path)
    context = sg.search(llm,
                        question='请问triviaqa 5shot结果怎么在summarizer里输出呢',
                        groupname='opencompass')
    print(context)
