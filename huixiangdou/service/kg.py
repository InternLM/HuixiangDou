import pytoml
from typing import List
from loguru import logger
from .llm_client import ChatClient
from .helper import extract_json_from_str
from .file_operation import FileOperation
from uuid import uuid4
import re
from dataclasses import dataclass, field
from enum import Enum, unique

@unique
class KGType(Enum):
    MARKDOWN = 'markdown'
    CHUNK = 'chunk'
    KEYWORD = 'keyword'
    IMAGE = 'image'

@dataclass
class Node:
    _type: KGType
    uuid: str = field(default_factory=uuid.uuid4)
    data: str = ''

@dataclass
class Relation:
    _from: str
    to: str
    desc: str

class KnowledgeGraph:
    def __init__(self, config_path: str):

        self.llm = ChatClient(config_path=config_path)
        self.nodes = []
        self.relations = []
        self.chunksize = 2048
        self.prompt_template = '你是一位语言专家，现在要做实体识别任务（NER），请阅读以下内容，以 json 形式输出实体：\n{}'
        self.md_pattern= re.compile(r'\[([^\]]+)\]\(([a-zA-Z0-9:/._~#-]+)?\)')
        with open(config_path) as f:
            config = pytoml.load(f)
            self.work_dir = config['feature_store']['work_dir']
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

    def build_md_chunk(self, md_node: Node, abspath: str):
        # get othernodes and relationship
        """
            {
                "entity": "HuixiangDou",
                "type": "Software"
            },
        """
        llm_raw_text = self.llm.generate_response(prompt=self.prompt_template.format(text))
        items = extract_json_from_str(raw=llm_raw_text)
        for item in items:
            # fetch nodes and add relations
            entity = item['entity']
            self.nodes.append(Node(uuid=entity, _type=KGType.KEYWORD))
            self.relations.append(Relation(entity, md_node.uuid, item['type']))

        file_opr = FileOperation()
        matches = self.md_pattern.findall(text)
        for match in matches:
            target = match[0]
            uri = match[1]
            if file_opr.get_type(uri) != 'image':
                continue

            if not uri.startswith('http'):
                uri = os.path.join(os.path.dirname(abspath), uri)
            uuid, image_path = file_opr.save_image(uri=uri, outdir=self.work_dir)
            if image_path is not None:
                self.nodes.append(Node(uuid=uuid, _type=KGType.IMAGE, data=image_path))
                self.relations.append(Relation(uuid, md_node.uuid, 'file'))


    def build_md(self, abspath: str):
        """Load markdown and split, build nodes and relationship."""
        content = ''
        with open(abspath) as f:
            content = f.read()
        splits = content.split('\n')
        
        chunk = ''
        pageid = 0

        md_node = Node(_type=KGType.MARKDOWN, data=abspath)
        self.nodes.append(md_node)

        def add_chunk(pageid=pageid, text: str):
            chunk_node = Node(_type=KGType.CHUNK, data=text)
            self.nodes.append(chunk_node)
            self.build_md_chunk(noded=chunk_node, abspath=abspath)
            self.relations.append(Relation(md_node.uuid, chunk_node.uuid, 'page{}'.format(pageid)))

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

    def save_svg(self):
        import networkx as nx
        G = nx.Graph()