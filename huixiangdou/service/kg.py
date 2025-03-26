
import argparse
import json
import os
import pdb
import pickle
import re
from dataclasses import asdict, dataclass, field
from enum import Enum, unique
from uuid import uuid4

import networkx as nx
import pytoml
from loguru import logger
from tqdm import tqdm

from ..primitive import FileOperation
from .helper import build_reply_text, extract_json_from_str
from .llm import LLM

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


def node_to_jsonstr(instance):
    dict_instance = asdict(instance)
    dict_instance['_type'] = instance._type.value
    return json.dumps(dict_instance, ensure_ascii=False)


@dataclass
class Relation:
    _from: str
    to: str
    desc: str


def relation_to_jsonstr(instance):
    dict_instance = asdict(instance)
    return json.dumps(dict_instance, ensure_ascii=False)


class KnowledgeGraph:

    def __init__(self,
                 config_path: str,
                 override: bool = False,
                 retry: int = 1):

        self.llm = LLM(config_path=config_path)
        self.retry = retry
        self.nodes = []
        self.relations = []
        self.chunksize = 2048
        self.prompt_template = '''
你是一位语言专家，现在要做实体识别任务（NER），请阅读以下内容，以 json 形式输出实体。直接给出结果不要解释。
输出示例：
[{"entity":"实体","type":"类型"}]

以下是阅读内容：
'''
        self.md_pattern = re.compile(r'\[([^\]]+)\]\(([a-zA-Z0-9:/._~#-]+)?\)')
        self.file_opr = FileOperation()
        self.override = override

        with open(config_path) as f:
            config = pytoml.load(f)
            self.kg_work_dir = os.path.join(
                config['feature_store']['work_dir'], 'kg')
            if not os.path.exists(self.kg_work_dir):
                os.makedirs(self.kg_work_dir)

        self.nodes_path = os.path.join(self.kg_work_dir, 'kg_nodes.jsonl')
        self.relations_path = os.path.join(self.kg_work_dir,
                                           'kg_relations.jsonl')
        self.gpickle_path = os.path.join(self.kg_work_dir, 'kg.gpickle')
        self.graph = None

    def build(self, repodir: str):
        logger.info(
            'multi-modal knowledge graph retrieval is experimental, only support markdown format.'
        )
        proc_files = []

        processed = []
        processed_path = os.path.join(self.kg_work_dir, 'processed.txt')
        if os.path.exists(processed_path):
            with open(processed_path) as f:
                for path in f:
                    processed.append(path.strip())

        for root, dirs, files in os.walk(repodir):
            for file in files:
                if '.github' in root:
                    continue
                file_type = self.file_opr.get_type(file)
                if file_type not in ['md']:
                    continue

                abspath = os.path.join(root, file)
                if abspath in processed:
                    logger.info(f'skip {abspath}')
                    continue
                proc_files.append((abspath, file_type))

        # save to jsonl and pickle
        if self.override:
            if os.path.exists(self.nodes_path):
                os.remove(self.nodes_path)
            if os.path.exists(self.relations_path):
                os.remove(self.relations_path)

        for abspath, file_type in tqdm(proc_files):
            if file_type == 'md':
                self.build_md(abspath)
            with open(processed_path, 'a') as f:
                f.write(abspath)
                f.write('\n')

            # save jsonl format
            with open(self.nodes_path, 'a') as f:
                for node in self.nodes:
                    f.write(node_to_jsonstr(node))
                    f.write('\n')
            self.nodes = []

            with open(self.relations_path, 'a') as f:
                for relation in self.relations:
                    f.write(relation_to_jsonstr(relation))
                    f.write('\n')
            self.relations = []

    async def build_md_chunk(self, md_node: Node, abspath: str):
        """Parse markdown chunk to nodes and relations.

        LLM NER with retry policy.
        """
        items = []
        for _ in range(self.retry):
            llm_raw_text = await self.llm.chat(
                prompt=self.prompt_template + md_node.data)
            items += extract_json_from_str(raw=llm_raw_text)

        if len(items) < 1:
            logger.warning(
                'parse llm_raw_text failed. {}'.format(llm_raw_text))
            return

        for item in items:
            # fetch nodes and add relations
            try:
                entity = item['entity']
                _type = item['type']
            except Exception as e:
                logger.error(e)
                logger.error(item)
                continue

            self.nodes.append(Node(uuid=entity, _type=KGType.KEYWORD))
            self.relations.append(Relation(entity, md_node.uuid, _type))

        matches = self.md_pattern.findall(md_node.data)
        for match in matches:
            # target = match[0]
            uri = match[1]
            if self.file_opr.get_type(uri) != 'image':
                continue

            if not uri.startswith('http'):
                uri = os.path.join(os.path.dirname(abspath), uri)
            uuid, image_path = self.file_opr.save_image(
                uri=uri, outdir=self.kg_work_dir)
            if image_path is not None:
                self.nodes.append(
                    Node(uuid=uuid, _type=KGType.IMAGE, data=image_path))
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

        def add_chunk(md_node: Node, pageid: int, text: str):
            chunk_node = Node(_type=KGType.CHUNK, data=text)
            self.nodes.append(chunk_node)
            self.build_md_chunk(md_node=chunk_node, abspath=abspath)
            self.relations.append(
                Relation(md_node.uuid, chunk_node.uuid,
                         'page{}'.format(pageid)))

        for split in splits:
            if len(split) >= self.chunksize:
                if len(chunk) > 0:
                    add_chunk(md_node=md_node, pageid=pageid, text=chunk)
                    pageid += 1
                    chunk = ''
                add_chunk(md_node=md_node, pageid=pageid, text=split)
                pageid += 1
                continue

            if len(chunk) + len(split) < self.chunksize:
                chunk = chunk + '\n' + split
                continue

            add_chunk(md_node=md_node, pageid=pageid, text=chunk)
            pageid += 1
            chunk = split

        if len(chunk) > 0:
            add_chunk(md_node=md_node, pageid=pageid, text=chunk)

    def dump_neo4j(self, uri: str, user: str, passwd: str):
        # Save networkx-neo4j for better graph viewer
        # Open `.config/Neo4j Desktop` and see https://neo4j.com/docs/operations-manual/current/configuration/ports/#_listen_address_configuration_settings
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, passwd))
        # clear database if override
        with driver.session() as session:
            session.run('MATCH (n) DETACH DELETE n')

        # load jsonl and save it
        nodes = dict()
        with open(self.nodes_path) as f:
            for json_str in f:
                node = json.loads(json_str)
                nodes[node['uuid']] = node

        add_node_query_with_props = """\
        MERGE (n:`%s` {`id`: $value })
        ON CREATE SET n+=$props
        """
        with driver.session() as session:
            for node in tqdm(nodes.values()):
                nodel_label = node['_type']
                query = add_node_query_with_props % nodel_label
                session.run(query, {'value': node['uuid']},
                            props={
                                'type': node['_type'],
                                'data': node['data']
                            })

        # load relations
        relations = []
        with open(self.relations_path) as f:
            for json_str in f:
                rel = json.loads(json_str)
                relations.append(rel)

        # query node1 and node2, add an relationship
        add_edge_query = """\
        MERGE (node1:`%s` {`id`: $node1 })
        MERGE (node2:`%s` {`id`: $node2 })
        MERGE (node1)-[r:`%s`]->(node2)
        ON CREATE SET r=$props
        """
        with driver.session() as session:
            for rel in tqdm(relations):
                _from = rel['_from']
                to = rel['to']

                label1 = nodes[_from]['_type']
                label2 = nodes[to]['_type']

                desc = rel['desc']
                if desc in ['file']:
                    relationship_type = desc
                elif desc.startswith('page'):
                    relationship_type = 'page'
                else:
                    relationship_type = 'attr'

                query = add_edge_query % (label1, label2, relationship_type)
                session.run(query, {
                    'node1': _from,
                    'node2': to
                },
                            props={'desc': desc})

    def dump_networkx(self):
        """Convert to networkx and dump GraphML format."""
        if not os.path.exists(self.nodes_path):
            logger.error('nodes path not exist')
            return

        if not os.path.exists(self.relations_path):
            logger.error('relations path not exist')
            return

        with open(self.nodes_path) as f:
            for json_str in f:
                self.nodes.append(json.loads(json_str))

        with open(self.relations_path) as f:
            for json_str in f:
                self.relations.append(json.loads(json_str))

        G = nx.Graph()
        for node in self.nodes:
            G.add_nodes_from([(node['uuid'], {
                'type': node['_type'],
                'data': node['data']
            })])
        for rel in self.relations:
            G.add_edge(rel['_from'], rel['to'], desc=rel['desc'])
        logger.debug(
            'Loaded knowledge graph, number of nodes {}, number of edges {}'.
            format(G.number_of_nodes(), G.number_of_edges()))

        # save to pickle format
        with open(self.gpickle_path, 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

    def is_available(self):
        """Check knowledge graph exist or not."""
        if os.path.exists(self.gpickle_path):
            return True
        return False

    def load(self):
        """Load knowledge graph."""
        if not os.path.exists(self.gpickle_path):
            logger.error('gpickle {} not exist.'.format(self.gpickle_path))
            return None

        with open(self.gpickle_path, 'rb') as f:
            self.graph = pickle.load(f)

        logger.debug('number of nodes {}, number of edges {}'.format(
            self.graph.number_of_nodes(), self.graph.number_of_edges()))

    def query_file_chunk_map(self, attr: str):
        ret = dict()

        G = self.graph
        # chunks = [G.nodes[neighbor] for neighbor in G.neighbors(attr)]
        for chunk in G.neighbors(attr):
            files = [
                nbr for nbr in G.neighbors(chunk)
                if 'page' in G.edges[chunk, nbr].get('desc')
            ]
            for file in files:
                chunk_data = G.nodes[chunk].get('data')
                file_data = G.nodes[file].get('data')
                if file_data in ret:
                    ret[file_data].append(chunk_data)
                else:
                    ret[file_data] = [chunk_data]

        return ret

    async def retrieve(self, query: str):
        if self.graph is None:
            self.load()
        llm_raw_text = await self.llm.chat(prompt=self.prompt_template + query)

        items = extract_json_from_str(raw=llm_raw_text)
        if len(items) < 1:
            return []

        file_chunks = dict()
        for item in items:
            # fetch nodes and add relations
            try:
                entity = item['entity']
                if not self.graph.has_node(entity):
                    continue

                file_chunks_on_entity = self.query_file_chunk_map(attr=entity)
                for k, v in file_chunks_on_entity.items():
                    if k in file_chunks:
                        file_chunks[k] += v
                    else:
                        file_chunks[k] = v

            except Exception as e:
                logger.error(e)
                logger.error(item)
                continue

        candidates = []
        for k, v in file_chunks.items():
            candidates.append({'path': k, 'chunks': v})

        candidates.sort(key=lambda x: len(x['chunks']))
        return candidates


def parse_args():
    """Parse command-line arguments.

    Please `export LOGURU_LEVEL=WARNING` before running.
    """
    parser = argparse.ArgumentParser(
        description='Knowledge graph for processing directories.')
    parser.add_argument('--repo_dir',
                        type=str,
                        default='repodir',
                        help='Root directory where the docs are located.')
    parser.add_argument('--config_path',
                        default='config.ini',
                        help='Configuration path. Default value is config.ini')
    parser.add_argument(
        '--override',
        action='store_true',
        default=False,
        help='Remove old data and rebuild knowledge graph from scratch.')
    parser.add_argument('--build',
                        action='store_true',
                        default=False,
                        help='Build knowledge graph from repodir.')
    parser.add_argument(
        '--dump-networkx',
        action='store_true',
        default=False,
        help='Load jsonl data and dump to networkx gpickle format.')
    parser.add_argument(
        '--dump-neo4j',
        action='store_true',
        default=False,
        help='Load jsonl data and dump to neo4j for viewing knowledge graph.')
    parser.add_argument('--neo4j-uri',
                        type=str,
                        default='bolt://10.1.52.85:7687',
                        help='neo4j URI, see https://neo4j.com/')
    parser.add_argument('--neo4j-user',
                        type=str,
                        default='neo4j',
                        help='neo4j username')
    parser.add_argument('--neo4j-passwd',
                        type=str,
                        default='neo4j',
                        help='neo4j password')
    parser.add_argument('--query',
                        type=str,
                        default=None,
                        help='Information Retrieval based on knowledge graph.')
    parser.add_argument('--retry',
                        type=int,
                        default=1,
                        help='Retry count for LLM NER.')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    kg = KnowledgeGraph(args.config_path,
                        override=args.override,
                        retry=args.retry)

    if args.build:
        kg.build(repodir=args.repo_dir)
        kg.dump_networkx()

    if args.dump_neo4j:
        kg.dump_neo4j(uri=args.neo4j_uri,
                      user=args.neo4j_user,
                      passwd=args.neo4j_passwd)

    if args.dump_networkx:
        kg.dump_networkx()

    if args.query:
        result = kg.retrieve(query=args.query)[0]
        reply_text = build_reply_text(code=0,
                                      query=args.query,
                                      reply=result['path'],
                                      refs=result['chunks'])
        logger.info('\n' + reply_text)
