"""Main entry point for the store module."""
from .store import parse_args, FeatureStore, test_reject, test_query
from .retriever import CacheRetriever
from ..primitive import FileOperation
import os
import json

if __name__ == '__main__':
    args = parse_args()
    cache = CacheRetriever(config_path=args.config_path)
    fs_init = FeatureStore(embedder=cache.embedder,
                           config_path=args.config_path,
                           override=args.override)

    # walk all files in repo dir
    file_opr = FileOperation()

    files = file_opr.scan_dir(repo_dir=args.repo_dir)

    fs_init.initialize(files=files, ner_file=args.ner_file, work_dir=args.work_dir)
    file_opr.summarize(files)
    del fs_init

    # update reject throttle
    retriever = cache.get(config_path=args.config_path, work_dir=args.work_dir)

    with open(os.path.join('resource', 'good_questions.json')) as f:
        good_questions = json.load(f)
    with open(os.path.join('resource', 'bad_questions.json')) as f:
        bad_questions = json.load(f)
    retriever.update_throttle(config_path=args.config_path,
                              good_questions=good_questions,
                              bad_questions=bad_questions)

    cache.pop('default')

    # test
    retriever = cache.get(config_path=args.config_path, work_dir=args.work_dir)
    test_reject(retriever, args.sample)
    test_query(retriever, args.sample)