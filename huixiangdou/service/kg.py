from typing import List
from loguru import logger
from .llm_client import ChatClient
from .helper import extract_json_from_str
from .file_operation import FileOperation
from .llm_server_hybrid import start_llm_server
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum, unique
import argparse
import os
import pdb
import pickle
import re
import pytoml
from tqdm import tqdm
import sys

def simple_uuid():
    return str(uuid4())[0:6]

@unique
class KGType(Enum):
    MARKDOWN = 'markdown'
    CHUNK = 'chunk'
    KEYWORD = 'keyword'
    IMAGE = 'image'

@dataclass
class Node:
    _type: KGType
    uuid: str = field(default_factory=simple_uuid)
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
        self.prompt_template = '''
你是一位语言专家，现在要做实体识别任务（NER），请阅读以下内容，以 json 形式输出实体。
输出示例：
[{"entity":"实体","type":"类型"}]

以下是阅读内容：
'''
        self.md_pattern= re.compile(r'\[([^\]]+)\]\(([a-zA-Z0-9:/._~#-]+)?\)')
        self.file_opr = FileOperation()

        with open(config_path) as f:
            config = pytoml.load(f)
            self.work_dir = config['feature_store']['work_dir']
            worker = config['worker']
        
    def build(self, repodir: str):
        logger.info('multi-modal knowledge graph retrieval is experimental, only support markdown format.')
        proc_files = []

        for root, dirs, files in os.walk(repodir):
            for file in files:
                file_type = self.file_opr.get_type(file)
                if file_type not in ['md']:
                    continue

                proc_files.append((os.path.join(root, file), file_type))

        for abspath, file_type in tqdm(proc_files):
            if file_type == 'md':
                self.build_md(abspath)

    def build_md_chunk(self, md_node: Node, abspath: str):
        # get othernodes and relationship
        """
            {
                "entity": "HuixiangDou",
                "type": "Software"
            },
        """
        llm_raw_text = self.llm.generate_response(prompt=self.prompt_template + md_node.data)
        items = extract_json_from_str(raw=llm_raw_text)
        if len(items) < 1:
            pdb.set_trace()
            logger.warning('parse llm_raw_text failed, please check. {}'.format(llm_raw_text))
        for item in items:
            # fetch nodes and add relations
            try:
                entity = item['entity']
            except Exception as e:
                pdb.set_trace()
                logger.error(e)

            self.nodes.append(Node(uuid=entity, _type=KGType.KEYWORD))
            self.relations.append(Relation(entity, md_node.uuid, item['type']))
        
        matches = self.md_pattern.findall(md_node.data)
        for match in matches:
            target = match[0]
            uri = match[1]
            if self.file_opr.get_type(uri) != 'image':
                continue

            if not uri.startswith('http'):
                uri = os.path.join(os.path.dirname(abspath), uri)
            uuid, image_path = self.file_opr.save_image(uri=uri, outdir=self.work_dir)
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

        def add_chunk(pageid:int, text: str):
            chunk_node = Node(_type=KGType.CHUNK, data=text)
            self.nodes.append(chunk_node)
            self.build_md_chunk(md_node=chunk_node, abspath=abspath)
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

    def dump_networkx(self, dump_path: str=None):
        """Convert to networkx and dump GraphML format"""
        import networkx as nx
        import matplotlib.pyplot as plt
        G = nx.Graph()
        for node in self.nodes:
            G.add_nodes_from([(node.uuid, {"type": node._type, "data": node.data})])
        for rel in self.relations:
            G.add_edge(rel._from, rel.to, desc=rel.desc)
        logger.debug('number of nodes {}, number of edges {}'.format(G.number_of_nodes(), G.number_of_edges()))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_shape='s')

        # save json format
        with open(os.path.join(self.work_dir, 'kg_nodes.json'), 'wb') as f:
            json_str = json.dumps(self.nodes, ensure_ascii=False)
            f.write(json_str)
        with open(os.path.join(self.work_dir, 'kg_relations.json'), 'wb') as f:
            json_str = json.dumps(self.relations, ensure_ascii=False)
            f.write(json_str)

        # save to pickle format
        with open(os.path.join(self.work_dir, 'kg.gpickle'), 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

        # save neo4j for better graph viewer
        # see https://neo4j.com/docs/operations-manual/current/configuration/ports/#_listen_address_configuration_settings
        # and open `.config/Neo4j Desktop`
        

    def dump_image_faiss(self):
        """Convert image to CLIP feature, save to faiss for later retriever"""
        pass

def parse_args():
    """Parse command-line arguments. Please `export LOGURU_LEVEL=WARNING` before running."""
    parser = argparse.ArgumentParser(
        description='Knowledge graph for processing directories.')
    parser.add_argument(
        '--repo_dir',
        type=str,
        default='repodir',
        help='Root directory where the docs are located.')
    parser.add_argument(
        '--config_path',
        default='config-kg.ini',
        help='Configuration path. Default value is config.ini')
    parser.add_argument(
        '--standalone',
        action='store_true',
        default=True,
        help='Building knowledge graph needs LLM for NER. This option would auto start LLM service, default value is True')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    if args.standalone:
        start_llm_server(args.config_path)
    kg = KnowledgeGraph(args.config_path)
    kg.build(args.repo_dir)
    kg.dump_networkx(args.dump_path)
