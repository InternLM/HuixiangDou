from huixiangdou.service import FeatureStore, CacheRetriever, Retriever, FileOperation
import os.path as osp
import argparse
import json
import re
from loguru import logger
from sklearn.metrics import precision_recall_curve, f1_score, recall_score, precision_score
from tqdm import tqdm

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Feature store for processing directories.')
    parser.add_argument('--work_dir',
                        type=str,
                        default='workdir',
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
    parser.add_argument(
        '--chunk-size', default=768, help='Text chunksize')
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

def calculate(config_path:str, repo_dir:str, work_dir: str, chunk_size: int = 768):
    # export PYTHONWARNINGS=ignore
    text_labels = load_dataset()

    # 按不同 chunk_size 和 chunk_size，构建特征库
    # 读 input.jsonl 计算 F1
    cache = CacheRetriever(config_path=config_path)
    fs_init = FeatureStore(embeddings=cache.embeddings,
                           reranker=cache.reranker,
                           config_path=config_path,
                           chunk_size=chunk_size)

    # walk all files in repo dir
    file_opr = FileOperation()
    files = file_opr.scan_dir(repo_dir=repo_dir)
    fs_init.preprocess(files=files, work_dir=work_dir)
    fs_init.ingress_reject(files=files, work_dir=work_dir)
    del fs_init

    retriever = CacheRetriever(config_path=config_path).get()

    start = 0.2
    stop = 0.8
    step = 0.1
    throttles = [round(start + step * i, 4) for i in range(int((stop - start) / step) + 1)]
    best_chunk_f1 = 0.0

    for throttle in tqdm(throttles):
        retriever.reject_throttle = throttle

        dts = []
        gts = []
        for text_label in text_labels:
            dt, _ = retriever.is_relative(question=text_label[0])
            dts.append(dt)
            gts.append(text_label[1])

        f1 = f1_score(gts, dts)
        f1 = round(f1, 4)
        precision = precision_score(gts, dts)
        precision = round(precision, 4)
        recall = recall_score(gts, dts)
        recall = round(recall, 4)

        logger.info((throttle, precision, recall, f1))

        data = {
            'throttle': throttle, 
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        json_str = json.dumps(data)
        with open(osp.join(osp.dirname(__file__), 'chunk_size{}.jsonl'.format(chunk_size)), 'a') as f:
            f.write(json_str)
            f.write('\n')

        if f1 > best_chunk_f1:
            best_chunk_f1 = f1
    return best_chunk_f1

def main():
    args = parse_args()
    best_f1 = 0.0
    best_chunk_size = -1
    for chunk_size in range(256, 8192, 256):
    # timecost 21 miniutes
        chunk_f1 = calculate(config_path=args.config_path, repo_dir=args.repo_dir, work_dir=args.work_dir, chunk_size=chunk_size)
        if chunk_f1 > best_f1:
            best_f1 = chunk_f1
            best_chunk_size = chunk_size

    logger.info(f'best_chunksize {best_chunk_size} f1 {best_f1}')

if __name__ == '__main__':
    main()