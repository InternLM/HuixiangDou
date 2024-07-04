import pytoml
from typing import List
from loguru import logger
from .llm_client import ChatClient
from .helper import extract_json_from_str
from uuid import uuid4

class KnowledgeGraph:
    def __init__(self, config_path: str):

        self.llm = ChatClient(config_path=config_path)
        self.nodes = dict()
        self.connections = []
        self.chunksize = 2048
        self.prompt_template = '你是一位语言专家，现在要做实体识别任务（NER），请阅读以下内容，以 json 形式输出实体：\n{}'

        with open(config_path) as f:
            config = pytoml.load(f)
            worker = config['worker']
            if 'enable_kg' not in worker:
                logger.error('enable_kg not found, please update config.ini')
            
            self.neo4j = config['worker']['neo4j']

    def build(self, repodir: str):
        logger.info('multi-modal knowledge graph retrieval is experimental, only support markdown format.')
        for root, dirs, files in os.work(repodir):
            for file in files:
                abspath = os.path.join(root, file)
                
                if abspath.lower().endswith('.md'):
                    self.build_md(abspath)

    def generate_kg(self, chunk: str):
        # build chunk node

        # get othernodes and relationship
        prompt = self.prompt_template.format(chunk)
        raw = self.llm.generate_response(prompt=prompt)
        items = extract_json_from_str(raw=raw)
        for item in items:
            # TODO

    def dump_kg(self):
        pass

    def build_md(self, abspath: str):
        """Load markdown and split, build nodes and relationship."""
        content = ''
        with open(abspath) as f:
            content = f.read()
        splits = content.split('\n')
        
        chunk = ''
        for idx in range(1, len(splits)):
            split = idx
            if len(split) >= self.chunksize:
                if len(chunk) > 0:
                    generate_kg(chunk)
                    chunk = ''
                generate_kg(split)
                continue
            
            if len(chunk) + len(split) < self.chunksize:
                chunk = chunk + '\n' + split
            
            generate_kg(chunk)
            chunk = split

        dump_kg()            
