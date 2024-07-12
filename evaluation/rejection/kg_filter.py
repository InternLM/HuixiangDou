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

from huixiangdou.service import KnowledgeGraph, start_llm_server, histogram

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

def summarize():
    # ('precision, recall, F1', 0.7324, 0.3427, 0.467)
    # 过于保守，导致许多正类样本被错误地分类为负类。
    # [0,+无穷) 的模式，叠加到 dense 结果上
    #
    # distribution:
    # 0-13  53.85%
    # 13-26  9.03%
    # 26-39  6.02%
    # 39-52  14.72%
    # 52-65  8.36%
    # 65-78  5.02%
    # 78-91  1.34%
    # 91-104  0.67%
    # 104-117  0.33%
    # 117-130  0.67%

    outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
    dts = []
    gts = []
    max_ref_cnts = []
    with open(outpath) as f:
        for line in f:
            json_obj = json.loads(line)
            gts.append(json_obj['gt'])
            if json_obj['result'] is None:
                dts.append(False)
                # max_ref_cnts.append(0)
            elif len(json_obj['result']) <=5:
                dts.append(False)
                # max_ref_cnts.append(0)
            else:
                dts.append(True)
                max_ref_cnts.append(len(json_obj['result']))

    logger.info(histogram(max_ref_cnts))
    f1 = f1_score(gts, dts)
    f1 = round(f1, 4)
    precision = precision_score(gts, dts)
    precision = round(precision, 4)
    recall = recall_score(gts, dts)
    recall = round(recall, 4)

    logger.info(('precision, recall, F1', precision, recall, f1))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Knowledge graph for processing directories.')
    parser.add_argument(
        '--config_path',
        default='config-kg.ini',
        help='Configuration path. Default value is config.ini')
    parser.add_argument(
        '--retrieve',
        default=False,
        help='Retrieve result from knowledge graph.')
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    if args.retrieve:
        start_llm_server(args.config_path)
        calculate(args.config_path)
    else:
        summarize()

if __name__ == '__main__':
    main()
