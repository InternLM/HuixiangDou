import pytoml
from typing import List
from loguru import logger
from .llm_client import ChatClient
from .helper import extract_json_from_str
from uuid import uuid4

class KnowledgeGraph:
    def __init__(self, config_path: str):

        self.llm = ChatClient(config_path=config_path)
        self.nodes = []
        self.relations = []
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

    def build_md_text(self, node: dict):
        # get othernodes and relationship
        """
            {
                "entity": "HuixiangDou",
                "type": "Software"
            },
        """
        uuid = node['uuid']
        text = node['text']
        prompt = self.prompt_template.format(text)
        raw = self.llm.generate_response(prompt=prompt)
        items = extract_json_from_str(raw=raw)
        for item in items:
            # fetch nodes and add relations
            entity = item['entity']
            self.nodes.append({'uuid': entity, 'type': 'keywords'})
            self.relations.append({
                'from': entity,
                'to': uuid,
                'relation': item['type']
            })

        # TODO parse image
        if '\[' in text and '\]' in text:
            # markdown formatted
            
        else:

            
    def build_md(self, abspath: str):
        """Load markdown and split, build nodes and relationship."""
        content = ''
        with open(abspath) as f:
            content = f.read()
        splits = content.split('\n')
        
        chunk = ''
        pageid = 0

        md_node = {
            'uuid': uuid4(),
            'data': abspath,
            'type': 'markdown'
        }
        self.nodes.append(md_node)

        def add_chunk(pageid=pageid, text: str):
            chunk_node = {
                'uuid': uuid4(),
                'data': text,
                'type': 'chunk'
            }
            self.nodes.append(chunk_node)
            self.build_md_text(chunk_node)
            self.relations.append({
                'from': md_node['uuid'],
                'to': chunk_node['uuid'],
                'relation': 'page{}'.format(pageid)
            })

        for split in splits:
            if len(split) >= self.chunksize:
                if len(chunk) > 0:
                    add_chunk(pageid=pageid, text=chunk)
                    pageid += 1
                    chunk = ''
                add_chunk(pageid=pageid, text=split)
                pageid +=1
                continue
            
            if len(chunk) + len(split) < self.chunksize:
                chunk = chunk + '\n' + split
                continue

            add_chunk(pageid=pageid, text=chunk)
            pageid +=1
            chunk = split

        dump_kg()            
