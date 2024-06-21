from huixiangdou.service import FeatureStore, CacheRetriever, Retriever, FileOperation
import os.path as osp
import argparse
import json
import re
from loguru import logger
from sklearn.metrics import precision_recall_curve, f1_score, recall_score, precision_score
from tqdm import tqdm
import multiprocessing
from multiprocessing import Pool, Process
import os
import pdb

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

def load_queries(fsid: str):
    query_path = os.path.join('/workspace/HuixiangDou/evaluation/queries/', fsid+'.txt')
    if not os.path.exists(query_path):
        return []
    queries = set()
    with open(query_path) as f:
        for line in f:
            queries.add(line)
    return list(queries)

def process(param:tuple):
    fsid, filedir = param
    queries = load_queries(fsid=fsid)
    if len(queries) < 1:
        return

    config_path = 'config.ini'
    cache = CacheRetriever(config_path=config_path)

    fs_init = FeatureStore(embeddings=cache.embeddings,
                           reranker=cache.reranker,
                           config_path=config_path)

    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=filedir)
    work_dir = os.path.join('workdir',fsid)
    fs_init.ingress_response(files=files, work_dir=work_dir)
    del fs_init

    retriever = CacheRetriever(config_path=config_path).get(fs_id=fsid, work_dir=work_dir)

    for query in queries:
        docs = retriever.compression_retriever.get_relevant_documents(query)
        for doc in docs:
            

def main():
    base = '/workspace/HuixiangDou/evaluation/feature_stores'
    dirs = os.listdir(base)
    params = []
    for fsid in dirs:
        filedir = os.path.join(base, fsid, 'workdir/preprocess')
        process(fsid=fsid, filedir=filedir)
        params.append((fsid, filedir))
    # pool = NestablePool(6)
    # result = pool.map(process, params)
    # pool.close()
    # pool.join()

if __name__ == '__main__':
    main()
