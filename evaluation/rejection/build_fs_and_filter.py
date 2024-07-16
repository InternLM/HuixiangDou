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

from huixiangdou.service import (CacheRetriever, FeatureStore, FileOperation)

save_hardcase = False

class KnowledgeGraphScore():
    def __init__(self, level:int):
        outpath = os.path.join(os.path.dirname(__file__), 'out.jsonl')
        self.scores = dict()
        with open(outpath) as f:
            for line in f:
                json_obj = json.loads(line)
                query = json_obj['query']
                
                score = 0.0
                result = json_obj['result']
                if result is not None and len(result) > level:
                    score = max(100, len(result) - level) / 100
                self.scores[query] = score
    
    def evaluate(self, query:str):
        return self.scores[query]


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
    parser.add_argument('--hybrid', default=False, help='Combine knowledge graph evaluation and dense feature score')
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
    cache = CacheRetriever(config_path=config_path)
    fs_init = FeatureStore(embeddings=cache.embeddings,
                           config_path=config_path,
                           chunk_size=chunk_size,
                           analyze_reject=True,
                           rejecter_naive_splitter=True)

    # walk all files in repo dir
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=repo_dir)
    # fs_init.preprocess(files=files, work_dir=work_dir)
    # fs_init.build_dense_response(files=files, work_dir=work_dir)
    # fs_init.build_dense_reject(files=files, work_dir=work_dir)
    # del fs_init

    retriever = CacheRetriever(config_path=config_path).get(
        fs_id=str(chunk_size), work_dir=work_dir)
    start = 0.4
    stop = 0.5
    step = 0.01
    throttles = [
        round(start + step * i, 4)
        for i in range(int((stop - start) / step) + 1)
    ]

    # start = 0.3
    # stop = 0.5
    # step = 0.01
    # throttles = [
    #     round(start + step * i, 4)
    #     for i in range(int((stop - start) / step) + 1)
    # ]

    best_chunk_f1 = 0.0
    best_level = 5

    for level in range(0, 50, 5):
        kg_score = KnowledgeGraphScore(level=level)
        for i in range(1, 4, 1):
            scale = i * 0.1
            for throttle in tqdm(throttles):
                retriever.reject_throttle = throttle

                dts = []
                gts = []
                for text_label in text_labels:
                    question = text_label[0]
                    
                    retriever.reject_throttle = max(0.0 , throttle - scale * kg_score.evaluate(query=question))
                    dt, _ = retriever.is_relative(question=question, disable_graph=True)
                    dts.append(dt)
                    gts.append(text_label[1])

                    if save_hardcase and dt != text_label[1]:
                        docs = retriever.compression_retriever.get_relevant_documents(
                            question)
                        if len(docs) > 0:
                            doc = docs[0]
                            question = question.replace('\n', ' ')
                            content = '{}  {}'.format(question, doc)
                            with open('hardcase{}.txt'.format(throttle), 'a') as f:
                                f.write(content)
                                f.write('\n')

                f1 = f1_score(gts, dts)
                f1 = round(f1, 4)
                precision = precision_score(gts, dts)
                precision = round(precision, 4)
                recall = recall_score(gts, dts)
                recall = round(recall, 4)

                logger.info((throttle, precision, recall, f1))

                data = {
                    'chunk_size': chunk_size,
                    'throttle': throttle,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }
                json_str = json.dumps(data)
                with open(
                        osp.join(osp.dirname(__file__),
                                'level{}_chunk_size{}.jsonl'.format(level, chunk_size)), 'a') as f:
                    f.write(json_str)
                    f.write('\n')

                if f1 > best_chunk_f1:
                    best_chunk_f1 = f1
                    best_level = level
    print(best_chunk_f1, best_level)
    return best_chunk_f1


def main():
    args = parse_args()
    best_f1 = 0.0
    best_chunk_size = -1

    calculate(832)
    # pool = NestablePool(6)
    # result = pool.map(calculate, range(128, 512, 32))
    # pool.close()
    # pool.join()
    # print(result)


if __name__ == '__main__':
    main()
