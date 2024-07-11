import argparse
import json
import multiprocessing
import os
import os.path as osp
import pdb
from multiprocessing import Pool, Process

from loguru import logger
from sklearn.metrics import (f1_score, precision_score,
                             recall_score)
from tqdm import tqdm

from huixiangdou.service import KnowledgeGraph, start_llm_server

def load_dataset():
    text_labels = []
    with open(osp.join(osp.dirname(__file__), 'gt_good.txt')) as f:
        for line in f:
            text_labels.append((line, True))

    with open(osp.join(osp.dirname(__file__), 'gt_bad.txt')) as f:
        for line in f:
            # rejection
            text_labels.append((line, False))

    return text_labels


def calculate(config_path: str = 'config.ini'):
    kg = KnowledgeGraph(config_path=config_path, override=False)
    G = kg.load_networkx()
    if not G:
        logger.error('Knowledge graph not build, quit.')
        return
    text_labels = load_dataset()
    
    outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
    for text, label in tqdm(text_labels):
        result = kg.retrieve(G=G, query=text)
        json_str = json.dumps({'query':text, 'result': result, 'gt': label}, ensure_ascii=False)
        with open(outpath, 'a') as f:
            f.write(json_str)
            f.write('\n')

def parse_args():
    parser = argparse.ArgumentParser(
        description='Knowledge graph for processing directories.')
    parser.add_argument(
        '--config_path',
        default='config-kg.ini',
        help='Configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    start_llm_server(args.config_path)
    calculate(args.config_path)

if __name__ == '__main__':
    main()
