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


class Record:
    def __init__(self, fsid: str):
        self.records = []
        self.fsid = fsid
        if os.path.exists('record.txt'):
            with open('record.txt') as f:
                for line in f:
                    self.records.append(f)
        
    def is_processed(self):
        if self.fsid in self.records:
            return True
        return False
    
    def mark_as_processed(self):
        with open('record.txt', 'a') as f:
            f.write(self.fsid)

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

    r = Record(fsid=fsid)
    if r.is_processed():
        return

    config_path = 'config.ini'
    cache = CacheRetriever(config_path=config_path)

    fs_init = FeatureStore(embeddings=cache.embeddings,
                           reranker=cache.reranker,
                           config_path=config_path)

    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=filedir)
    work_dir = os.path.join('workdir',fsid)
    fs_init.initialize(files=files, work_dir=work_dir)
    file_opr.summarize(files)
    del fs_init

    retriever = cache.get(config_path=config_path, work_dir=work_dir)
    
    if not os.path.exists('candidates'):
        os.makedirs('candidates')
    
    for query in queries:
        try:
            if len(query) > 512:
                import pdb
                pdb.set_trace()
                logger.info('long query: {}'.format(query))

            docs = retriever.compression_retriever.get_relevant_documents(query)
            candidates = []
            logger.info('{} docs count {}'.format(fsid, len(docs)))

            for doc in docs:
                data = {
                    'content': doc.page_content,
                    'source': doc.metadata['read'],
                    'score': doc.metadata['relevance_score']
                }
                candidates.append(data)

            json_str = json.dumps({'query': query, 'candidates': candidates}, ensure_ascii=False)

            with open(os.path.join('candidates', fsid+'.jsonl'), 'a') as f:
                f.write(json_str)
                f.write('\n')
        except Exception as e:
            pdb.set_trace()
            print(e)
    r.mark_as_processed()

def main():
    base = '/workspace/HuixiangDou/evaluation/feature_stores'
    dirs = os.listdir(base)
    params = []
    for fsid in dirs:
        filedir = os.path.join(base, fsid, 'workdir/preprocess')
        process((fsid,filedir))
        params.append((fsid, filedir))
    # pool = NestablePool(6)
    # result = pool.map(process, params)
    # pool.close()
    # pool.join()

if __name__ == '__main__':
    main()
