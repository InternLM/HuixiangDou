import argparse
import json
import multiprocessing
import os
import os.path as osp
import pdb
import random
import re
import string
from multiprocessing import Pool, Process

import numpy as np
from loguru import logger
from pymilvus import (AnnSearchRequest, Collection, CollectionSchema, DataType,
                      FieldSchema, RRFRanker, WeightedRanker, connections, db,
                      utility)
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from sklearn.metrics import (f1_score, precision_recall_curve, precision_score,
                             recall_score)
from tqdm import tqdm

from huixiangdou.service import (CacheRetriever, FeatureStore, FileOperation,
                                 Retriever)


class NoDaemonProcess(multiprocessing.Process):

    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass


class NoDaemonContext(type(multiprocessing.get_context())):
    Process = NoDaemonProcess


# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class NestablePool(multiprocessing.pool.Pool):

    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super(NestablePool, self).__init__(*args, **kwargs)


from pymilvus.model.hybrid import BGEM3EmbeddingFunction

ef = BGEM3EmbeddingFunction(model_name='/data2/khj/bge-m3',
                            use_fp16=False,
                            device='cuda',
                            batch_size=64)
dense_dim = ef.dim['dense']


def init_milvus(col_name: str, max_length_bytes: int):
    conn = connections.connect('default', host='localhost', port='19530')
    # Specify the data schema for the new Collection.
    fields = [
        # Use auto generated id as primary key
        FieldSchema(name='pk',
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    auto_id=True,
                    max_length=100),
        # Store the original text to retrieve based on semantically distance
        FieldSchema(name='text',
                    dtype=DataType.VARCHAR,
                    max_length=max_length_bytes),
        # Milvus now supports both sparse and dense vectors, we can store each in
        # a separate field to conduct hybrid search on both vectors.
        FieldSchema(name='sparse_vector', dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name='dense_vector',
                    dtype=DataType.FLOAT_VECTOR,
                    dim=dense_dim),
    ]
    schema = CollectionSchema(fields, '')
    # Now we can create the new collection with above name and schema.
    # col = Collection(col_name)
    # col.drop()
    col = Collection(col_name, schema, consistency_level='Strong')

    # We need to create indices for the vector fields. The indices will be loaded
    # into memory for efficient search.
    sparse_index = {'index_type': 'SPARSE_INVERTED_INDEX', 'metric_type': 'IP'}
    col.create_index('sparse_vector', sparse_index)
    dense_index = {'index_type': 'FLAT', 'metric_type': 'IP'}
    col.create_index('dense_vector', dense_index)
    col.load()
    return col


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Feature store for processing directories.')
    parser.add_argument('--work_dir_base',
                        type=str,
                        default='workdir basename',
                        help='Working directory.')
    parser.add_argument(
        '--repo_dir',
        type=str,
        default='repodir',
        help='Root directory where the repositories are located.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Feature store configuration path. Default value is config.ini')
    parser.add_argument('--chunk-size', default=768, help='Text chunksize')
    args = parser.parse_args()
    return args


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


def split_by_group(inputs: list, groupsize: int = 1024):
    # 计算需要分割成多少个小列表
    num_sublists = len(inputs) // groupsize
    remaining_items = len(inputs) % groupsize

    # 创建一个空列表来存储所有分割后的小列表
    sublists = []

    # 循环分割原始列表
    for i in range(num_sublists):
        # 计算每个小列表的起始和结束索引
        start_index = i * groupsize
        end_index = start_index + groupsize
        # 将原始列表的相应部分添加到子列表中
        sublists.append(inputs[start_index:end_index])

    # 如果原始列表长度不是256的整数倍，还需要添加剩余的部分
    if remaining_items > 0:
        sublists.append(inputs[num_sublists * groupsize:])

    # 现在 sublists 包含了分割后的所有小列表
    gt = len(inputs)
    dt = 0
    for lis in sublists:
        dt += len(lis)
    assert gt == dt

    return sublists


def calculate(chunk_size: int):
    config_path = 'config.ini'
    repo_dir = 'repodir'
    work_dir_base = 'workdir'
    work_dir = work_dir_base + str(chunk_size)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    # export PYTHONWARNINGS=ignore
    text_labels = load_dataset()

    # 按不同 chunk_size 和 chunk_size，构建特征库
    # 读 input.jsonl 计算 F1
    fs_init = FeatureStore(embeddings=None,
                           config_path=config_path,
                           chunk_size=chunk_size,
                           analyze_reject=True,
                           rejecter_naive_splitter=True)

    # walk all files in repo dir
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=repo_dir)
    fs_init.preprocess(files=files, work_dir=work_dir)
    docs = fs_init.build_dense_reject(files=files, work_dir=work_dir)
    del fs_init

    # docs = docs[0:20]

    col = init_milvus(col_name='test2', max_length_bytes=3 * chunk_size)

    subdocs = split_by_group(docs)
    pdb.set_trace()
    for idx, docs in enumerate(subdocs):
        print('build step {}'.format(idx))
        texts = []
        sources = []
        reads = []
        for doc in docs:
            texts.append(doc.page_content[0:chunk_size])
            sources.append(doc.metadata['source'])
            reads.append(doc.metadata['read'])

        max_length = len(max(texts, key=lambda x: len(x)))
        docs_emb = ef(texts)
        entities = [texts, docs_emb['sparse'], docs_emb['dense']]
        try:
            col.insert(entities)
            col.flush()
        except Exception as e:
            print(e)
            pdb.set_trace()

    print('insert finished')
    # start = 0.4
    # stop = 0.8
    # step = 0.05
    # throttles = [round(start + step * i, 4) for i in range(int((stop - start) / step) + 1)]

    start = 0.05
    stop = 0.5
    step = 0.05
    sparse_ratios = []
    sparse_ratios = [
        round(start + step * i, 4)
        for i in range(int((stop - start) / step) + 1)
    ]

    best_chunk_f1 = 0.0

    dts = []
    gts = []
    predictions = []
    labels = []

    for sparse_ratio in sparse_ratios:
        for text_label in tqdm(text_labels):

            query_embeddings = ef([text_label[0]])
            # 4. search and inspect the result!
            k = 1  # we want to get the top 2 docs closest to the query
            # Prepare the search requests for both vector fields
            sparse_req = AnnSearchRequest(query_embeddings['sparse'],
                                          'sparse_vector',
                                          {'metric_type': 'IP'},
                                          limit=k)
            dense_req = AnnSearchRequest(query_embeddings['dense'],
                                         'dense_vector', {'metric_type': 'IP'},
                                         limit=k)

            # Search topK docs based on dense and sparse vectors and rerank with RRF.
            res = col.hybrid_search([sparse_req, dense_req],
                                    rerank=WeightedRanker(
                                        sparse_ratio, 1.0 - sparse_ratio),
                                    limit=k,
                                    output_fields=['text'])

            # Currently Milvus only support 1 query in the same hybrid search request, so
            # we inspect res[0] directly. In future release Milvus will accept batch
            # hybrid search queries in the same call.
            res = res[0]
            if len(res) > 0:
                predictions.append(max(0.0, min(1.0, res[0].score)))
            else:
                predictions.append(0)

            if text_label[1]:
                labels.append(1)
            else:
                labels.append(0)

        precision, recall, thresholds = precision_recall_curve(
            labels, predictions)
        f1 = 2 * precision * recall / (precision + recall)
        logger.debug('sparse_ratio {} max f1 {} at {}, threshold {}'.format(
            sparse_ratio, np.max(f1), np.argmax(f1),
            thresholds[np.argmax(f1)]))


def main():
    args = parse_args()
    best_f1 = 0.0
    best_chunk_size = -1

    calculate(2048)
    # pool = NestablePool(6)
    # result = pool.map(calculate, range(128, 512, 32))
    # pool.close()
    # pool.join()
    # print(result)


if __name__ == '__main__':
    main()
