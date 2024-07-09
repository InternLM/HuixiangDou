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
import json

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
            self.kg_work_dir = os.path.join(config['feature_store']['work_dir'])
            if not os.path.exists(self.kg_work_dir):
                os.makedirs(self.kg_work_dir)
        
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
            logger.warning('parse llm_raw_text failed, please check. {}'.format(llm_raw_text))
            return

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
            uuid, image_path = self.file_opr.save_image(uri=uri, outdir=self.kg_work_dir)
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

    def dump_neo4j(self, uri: str, user: str, passwd: str):
        # Save networkx-neo4j for better graph viewer
        # Open `.config/Neo4j Desktop` and see https://neo4j.com/docs/operations-manual/current/configuration/ports/#_listen_address_configuration_settings
        # See https://github.com/jbaktir/networkx-neo4j/blob/master/examples/nxneo4j_tutorial_latest.ipynb
        from neo4j import GraphDatabase
        import nxneo4j as nx
        driver = GraphDatabase.driver(uri, auth=(user, password))
        G = nx.Graph(driver)
        # clear database first
        G.delete_all()

        # load jsonl and save it
        nodes_path = os.path.join(self.kg_work_dir, 'kg_nodes.jsonl')
        relations_path = os.path.join(self.kg_work_dir, 'kg_relations.jsonl')

        with open(nodes_path) as f:
            for json_str in f:
                node = json.loads(json_str)
                G.add_nodes_from([(node.uuid, {"type": node._type, "data": node.data})])
            
        with open(relations_path) as f:
            for json_str in f:
                rel = json.loads(json_str)
                G.add_edge(rel._from, rel.to, desc=rel.desc)

    def dump_networkx(self, override:bool=False):
        """Convert to networkx and dump GraphML format"""
        import networkx as nx
        import matplotlib.pyplot as plt

        G = nx.Graph()
        for node in self.nodes:
            G.add_nodes_from([(node.uuid, {"type": node._type, "data": node.data})])
        for rel in self.relations:
            G.add_edge(rel._from, rel.to, desc=rel.desc)
        logger.debug('number of nodes {}, number of edges {}'.format(G.number_of_nodes(), G.number_of_edges()))

        # save to jsonl and pickle
        nodes_path = os.path.join(self.kg_work_dir, 'kg_nodes.jsonl')
        relations_path = os.path.join(self.kg_work_dir, 'kg_relations.jsonl')

        pdb.set_trace()
        if override:
            if os.path.exists(nodes_path):
                os.remove(nodes_path) 
            if os.path.exists(relations_path):
                os.remove(relations_path)
        
        # save jsonl format
        with open(nodes_path, 'a') as f:
            for node in self.nodes:
                json_str = json.dumps(self.node, ensure_ascii=False)
                f.write(json_str)
                f.write('\n')

        with open(relations_path, 'a') as f:
            for relation in self.relations:
                json_str = json.dumps(self.relation, ensure_ascii=False)
                f.write(json_str)
                f.write('\n')

        # save to pickle format
        gpick_path = os.path.join(self.kg_work_dir, 'kg-{}.gpickle'.format(round(time.time())))
        with open(gpick_path, 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

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
    parser.add_argument(
        '--override',
        action='store_true',
        default=True,
        help='Remove old data and rebuild knowledge graph from scratch.')
    parser.add_argument(
        '--dump-neo4j',
        action='store_true',
        default=False,
        help='Load jsonl data and dump to neo4j for viewing knowledge graph.')
    parser.add_argument(
        '--neo4j-uri',
        type=str,
        default='bolt://10.1.52.85:7687',
        help='neo4j URI, see https://neo4j.com/')
    parser.add_argument(
        '--neo4j-user',
        type=str,
        default='neo4j',
        help='neo4j username, see https://neo4j.com/')
    parser.add_argument(
        '--neo4j-passwd',
        type=str,
        default='neo4j',
        help='neo4j password, see https://neo4j.com/')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    if args.standalone:
        start_llm_server(args.config_path)
    kg = KnowledgeGraph(args.config_path)
    kg.build(repodir=args.repo_dir)
    kg.dump_networkx(override=args.override)

    if args.dump_neo4j:
        kg.dump_neo4j(uri=args.neo4j_uri, user=args.neo4j_user, passwd=args.neo4j_passwd)
