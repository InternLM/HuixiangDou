from huixiangdou.service import FeatureStore, CacheRetriever, Retriever, FileOperation
import os.path as osp
import argparse
import json
import re
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
        '--good_questions',
        default='resource/good_questions.json',
        help=  # noqa E251
        'Positive examples in the dataset. Default value is resource/good_questions.json'  # noqa E501
    )
    parser.add_argument(
        '--bad_questions',
        default='resource/bad_questions.json',
        help=  # noqa E251
        'Negative examples json path. Default value is resource/bad_questions.json'  # noqa E501
    )
    parser.add_argument(
        '--chunk-size', default=768, help='Text chunksize')
    args = parser.parse_args()
    return args

def main():
    texts = []
    with open(osp.join(osp.dirname(__file__), 'input.jsonl')) as f:
        for line in f:
            json_obj = json.loads(line)
            if 'text' not in json_obj:
                continue

            text = json_obj['text']
            if len(text) < 1:
                continue

            text = re.sub(r'\n', ' ', text)
            text = text.strip()
            
            if text in texts:
                continue
                
            texts.append(text)

    # 按不同 chunk_size 和 chunk_size，构建特征库
    # 读 input.jsonl 计算 F1
    args = parse_args()
    cache = CacheRetriever(config_path=args.config_path)
    fs_init = FeatureStore(embeddings=cache.embeddings,
                           reranker=cache.reranker,
                           config_path=args.config_path,
                           chunk_size=args.chunk_size)

    # walk all files in repo dir
    file_opr = FileOperation()
    # files = file_opr.scan_dir(repo_dir=args.repo_dir)
    # fs_init.preprocess(files=files, work_dir=args.work_dir)
    # fs_init.ingress_reject(files=files, work_dir=args.work_dir)
    del fs_init

    retriever = CacheRetriever(config_path=args.config_path).get()

    for text in texts:
        reject, docs = retriever.is_reject(question=text)
        if len(text) < 7 or reject is True:
            with open(osp.join(osp.dirname(__file__), 'bad.txt'), 'a') as f:
                f.write(r'{}'.format(text))
                f.write('\n')
        else:
            print(len(text))
            with open(osp.join(osp.dirname(__file__), 'good.txt'), 'a') as f:
                f.write(r'{}'.format(text))
                f.write('\n')

if __name__ == '__main__':
    main()