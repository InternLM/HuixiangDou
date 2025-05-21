"""extract feature and search with user query."""
import argparse
import json
import os
import pdb
import re
import shutil
import time
import csv
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Any, Dict, List, Optional, Tuple
import random
import pytoml
from loguru import logger
from tqdm import tqdm


from ..primitive import (ChineseRecursiveTextSplitter, Chunk, Embedder, Faiss,
                         FileName, FileOperation,
                         RecursiveCharacterTextSplitter, nested_split_markdown,
                         split_python_code,
                         BM25Okapi, NamedEntity2Chunk)
from .helper import histogram
from .retriever import CacheRetriever, Retriever


@dataclass
class InitializeConfig:
    """Configuration for initializing the feature store."""
    files: List[FileName]
    work_dir: str
    ner_file: Optional[str] = None
    qa_pair_file: Optional[str] = None

def empty_cache():
    try:
        from torch.cuda import empty_cache as cuda_empty_cache
        cuda_empty_cache()
    except Exception as e:
        logger.error(e)


def read_and_save(file: FileName):
    if os.path.exists(file.copypath):
        # already exists, return
        logger.info('already exist, skip load')
        return
    file_opr = FileOperation()
    logger.info('reading {}, would save to {}'.format(file.origin,
                                                      file.copypath))
    content, error = file_opr.read(file.origin)
    if error is not None:
        logger.error('{} load error: {}'.format(file.origin, str(error)))
        return

    if content is None or len(content) < 1:
        logger.warning('{} empty, skip save'.format(file.origin))
        return

    with open(file.copypath, 'w') as f:
        f.write(content)


class FeatureStore:
    """Tokenize and extract features from the project's documents, for use in
    the reject pipeline and response pipeline."""

    def __init__(self,
                 embedder: Embedder,
                 config_path: str = 'config.ini',
                 language: str = 'zh',
                 chunk_size=900,
                 analyze_reject=False,
                 rejecter_naive_splitter=False,
                 override=False) -> None:
        """Init with model device type and config."""
        self.config_path = config_path
        self.reject_throttle = -1
        self.language = language
        self.override = override
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)['feature_store']
            self.reject_throttle = config['reject_throttle']

        logger.debug('loading text2vec model..')
        self.embedder = embedder
        self.retriever = None
        self.chunk_size = chunk_size
        self.analyze_reject = analyze_reject

        if rejecter_naive_splitter:
            raise ValueError(
                'The `rejecter_naive_splitter` option deprecated, please `git checkout v20240722`'
            )

        if analyze_reject:
            raise ValueError(
                'The `analyze_reject` option deprecated, please `git checkout v20240722`'
            )

        logger.info('init dense retrieval database with chunk_size {}'.format(chunk_size))

        if language == 'zh':
            self.text_splitter = ChineseRecursiveTextSplitter(
                keep_separator=True,
                is_separator_regex=True,
                chunk_size=chunk_size,
                chunk_overlap=32)
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=32)

    def parse_markdown(self, file: FileName, metadata: Dict):
        length = 0
        text = file.basename + '\n'

        with open(file.copypath, encoding='utf8') as f:
            text += f.read()
        if len(text) <= 1:
            return [], length

        chunks = nested_split_markdown(file.origin,
                                       text=text,
                                       chunksize=self.chunk_size,
                                       metadata=metadata)
        for c in chunks:
            length += len(c.content_or_path)
        return chunks, length
    
    def build_inverted_index(self, chunks: List[Chunk], ner_file: str, work_dir: str):
        """Build inverted index based on named entity for knowledge base."""
        if ner_file is None:
            return
        # 倒排索引 retrieve 建库
        index_dir = os.path.join(work_dir, 'db_reverted_index')
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        entities = []
        with open(ner_file) as f:
            entities = json.load(f)
            
        time0 = time.time()
        map_entity2chunks = dict()
        indexer = NamedEntity2Chunk(file_dir=index_dir)
        indexer.clean()
        indexer.set_entity(entities=entities)
        
        # build inverted index
        for chunk_id, chunk in enumerate(chunks):
            if chunk.modal != 'text':
                continue
            entity_ids = indexer.parse(text=chunk.content_or_path)
            for entity_id in entity_ids:
                if entity_id not in map_entity2chunks:
                    map_entity2chunks[entity_id] = [chunk_id]
                else:
                    map_entity2chunks[entity_id].append(chunk_id)
    
        for entity_id, chunk_indexes in map_entity2chunks.items():
            indexer.insert_relation(eid = entity_id, chunk_ids=chunk_indexes)
        del indexer
        time1 = time.time()
        logger.info('Timecost for build_inverted_index {}s'.format(time1-time0))
        
    def build_sparse(self, files: List[FileName], work_dir: str):
        """Use BM25 for building code feature"""
        # split by function, class and annotation, remove blank
        # build bm25 pickle
        fileopr = FileOperation()
        chunks = []
        
        for file in files:
            content, error = fileopr.read(file.origin)
            if error is not None:
                continue
            file_chunks = split_python_code(filepath=file.origin, text=content, metadata={'source': file.origin, 'read': file.copypath})
            chunks += file_chunks
        
        sparse_dir = os.path.join(work_dir, 'db_sparse')
        bm25 = BM25Okapi()
        bm25.save(chunks, sparse_dir)

    def process_qa_pairs(self, qa_pair_file: str) -> List[Chunk]:
        """Process QA pairs from CSV or JSON file.
        
        Args:
            qa_pair_file: Path to the CSV or JSON file containing QA pairs.
            
        Returns:
            List of Chunk objects where key is the content and value is stored in metadata.
        """
        chunks = []
        file_ext = os.path.splitext(qa_pair_file)[1].lower()
        
        try:
            if file_ext == '.csv':
                # Process CSV file - first column is key, second column is value
                with open(qa_pair_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    for row in csv_reader:
                        if len(row) >= 2:
                            key, value = row[0], row[1]
                            # Create a chunk with key as content and value in metadata
                            chunk = Chunk(
                                content_or_path=key,
                                metadata={'source': qa_pair_file, 'value': value}
                            )
                            chunks.append(chunk)
            
            elif file_ext == '.json':
                # Process JSON file
                with open(qa_pair_file, 'r', encoding='utf-8') as f:
                    qa_data = json.load(f)
                    
                    # Handle different JSON formats
                    if isinstance(qa_data, dict):
                        # Format: {"key1": "value1", "key2": "value2", ...}
                        for key, value in qa_data.items():
                            chunk = Chunk(
                                content_or_path=key,
                                metadata={'source': qa_pair_file, 'value': value}
                            )
                            chunks.append(chunk)
                    elif isinstance(qa_data, list):
                        # Format: [{"key": "key1", "value": "value1"}, ...]
                        for item in qa_data:
                            if isinstance(item, dict) and 'key' in item and 'value' in item:
                                chunk = Chunk(
                                    content_or_path=item['key'],
                                    metadata={'source': qa_pair_file, 'value': item['value']}
                                )
                                chunks.append(chunk)
            
            logger.info(f"Processed {len(chunks)} QA pairs from {qa_pair_file}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing QA pairs from {qa_pair_file}: {str(e)}")
            return []

    def build_dense(self, files: List[FileName], work_dir: str, markdown_as_txt: bool=False, qa_pair_file: str = None):
        """Extract the features required for the response pipeline based on the
        document."""
        feature_dir = os.path.join(work_dir, 'db_dense')
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)

        file_opr = FileOperation()
        chunks = []
        
        # Process QA pairs if provided
        if qa_pair_file is not None:
            qa_chunks = self.process_qa_pairs(qa_pair_file)
            chunks.extend(qa_chunks)
            logger.info(f"Added {len(qa_chunks)} chunks from QA pairs")
        
        # Process regular files
        for i, file in tqdm(enumerate(files), 'split'):
            if not file.state:
                continue
            metadata = {'source': file.origin, 'read': file.copypath}

            # If you need higher rejection precision, set `markdown_as_txt` as True
            if not markdown_as_txt and file._type == 'md':
                md_chunks, md_length = self.parse_markdown(file=file,
                                                           metadata=metadata)
                chunks += md_chunks
                file.reason = str(md_length)

            else:
                # now read pdf/word/excel/ppt text
                text, error = file_opr.read(file.copypath)
                if error is not None:
                    file.state = False
                    file.reason = str(error)
                    continue
                file.reason = str(len(text))
                text = file.prefix + text
                chunks += self.text_splitter.create_chunks(
                    texts=[text], metadatas=[metadata])

        if not self.embedder.support_image:
            filtered_chunks = list(filter(lambda x: x.modal=='text', chunks))
        else:
            filtered_chunks = chunks
        if len(chunks) < 1:
            return chunks

        self.analyze(filtered_chunks)
        Faiss.save_local(folder_path=feature_dir, chunks=filtered_chunks, embedder=self.embedder)
        return chunks

    def analyze(self, chunks: List[Chunk]):
        """Output documents length mean, median and histogram."""
        MAX_COUNT = 10000
        if len(chunks) > MAX_COUNT:
            chunks = random.sample(chunks, MAX_COUNT)

        text_lens = []
        token_lens = []
        text_chunk_count = 0
        image_chunk_count = 0

        if self.embedder is None:
            logger.info('self.embedder is None, skip `anaylze_output`')
            return
        for chunk in tqdm(chunks, 'analyze distribution'):
            if chunk.modal == 'image':
                image_chunk_count += 1
            elif chunk.modal == 'text':
                text_chunk_count += 1

            content = chunk.content_or_path
            text_lens.append(len(content))
            token_lens.append(self.embedder.token_length(content))

        logger.info('text_chunks {}, image_chunks {}'.format(text_chunk_count, image_chunk_count))
        logger.info('text histogram, {}'.format(histogram(text_lens)))
        logger.info('token histogram, {}'.format(
            histogram(token_lens)))

    def preprocess(self, files: List, work_dir: str):
        """Preprocesses files in a given directory. Copies each file to
        'preprocess' with new name formed by joining all subdirectories with
        '_'.

        Args:
            files (list): original file list.
            work_dir (str): Working directory where preprocessed files will be stored.  # noqa E501

        Returns:
            str: Path to the directory where preprocessed markdown files are saved.

        Raises:
            Exception: Raise an exception if no markdown files are found in the provided repository directory.  # noqa E501
        """
        preproc_dir = os.path.join(work_dir, 'preprocess')
        if not os.path.exists(preproc_dir):
            os.makedirs(preproc_dir)

        pool = Pool(processes=8)
        file_opr = FileOperation()
        for idx, file in tqdm(enumerate(files), 'preprocess'):
            if not os.path.exists(file.origin):
                file.state = False
                file.reason = 'skip not exist'
                continue

            if file._type == 'image':
                file.state = False
                file.reason = 'skip image'

            elif file._type in ['pdf', 'word', 'excel', 'ppt', 'html']:
                # read pdf/word/excel file and save to text format
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir,
                                             '{}.text'.format(md5))
                pool.apply_async(read_and_save, (file, ))

            elif file._type in ['code']:
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(preproc_dir,
                                             '{}.code'.format(md5))
                read_and_save(file)

            elif file._type in ['md', 'text']:
                # rename text files to new dir
                md5 = file_opr.md5(file.origin)
                file.copypath = os.path.join(
                    preproc_dir,
                    file.origin.replace('/', '_')[-84:])
                try:
                    shutil.copy(file.origin, file.copypath)
                    file.state = True
                    file.reason = 'preprocessed'
                except Exception as e:
                    file.state = False
                    file.reason = str(e)
            else:
                file.state = False
                file.reason = 'skip unknown format'
        pool.close()
        logger.debug('waiting for file preprocess finish..')
        pool.join()

        # check process result
        for file in files:
            if file._type in ['pdf', 'word', 'excel']:
                if os.path.exists(file.copypath):
                    file.state = True
                    file.reason = 'preprocessed'
                else:
                    file.state = False
                    file.reason = 'read error'

    def initialize(self, config: InitializeConfig):
        """Initializes response and reject feature store.

        Only needs to be called once. Also calculates the optimal threshold
        based on provided good and bad question examples, and saves it in the
        configuration file.
        
        Args:
            config: Configuration object containing initialization parameters
        """
        logger.info(
            'initialize response and reject feature store, you only need call this once.'  # noqa E501
        )
        self.preprocess(files=config.files, work_dir=config.work_dir)
        # build dense retrieval refusal-to-answer and response database
        documents = list(filter(lambda x: x._type != 'code', config.files))
        chunks = self.build_dense(files=documents, work_dir=config.work_dir, qa_pair_file=config.qa_pair_file)

        codes = list(filter(lambda x: x._type == 'code', config.files))
        self.build_sparse(files=codes, work_dir=config.work_dir)
        self.build_inverted_index(chunks=chunks, ner_file=config.ner_file, work_dir=config.work_dir)

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
        '--ner-file',
        default=None,
        help='The path of NER file, which is a dumped json list. HuixiangDou would build relationship between entities and chunks for retrieve.'
    )
    parser.add_argument(
        '--qa-pair',
        default=None,
        help='Path to a CSV or JSON file containing QA pairs. For CSV, the first column is the key and the second column is the value. For JSON, the format should be {"key":"value"} or a list of {"key":"key1", "value":"value1"}.'
    )
    parser.add_argument(
        '--sample', help='Input an json file, save reject and search output.')
    parser.add_argument(
        '--override',
        action='store_true',
        default=False,
        help='Remove old data and rebuild knowledge graph from scratch.')
    args = parser.parse_args()
    return args

def test_reject(retriever: Retriever, sample: str = None):
    """Simple test reject pipeline."""
    if sample is None:
        real_questions = [
            'SAM 10个T 的训练集，怎么比比较公平呢~？速度上还有缺陷吧？',
            '想问下，如果只是推理的话，amp的fp16是不会省显存么，我看parameter仍然是float32，开和不开推理的显存占用都是一样的。能不能直接用把数据和model都 .half() 代替呢，相比之下amp好在哪里',  # noqa E501
            'mmdeploy支持ncnn vulkan部署么，我只找到了ncnn cpu 版本',
            '大佬们，如果我想在高空检测安全帽，我应该用 mmdetection 还是 mmrotate',
            '请问 ncnn 全称是什么',
            '有啥中文的 text to speech 模型吗?',
            '今天中午吃什么？',
            'huixiangdou 是什么？',
            'mmpose 如何安装？',
            '使用科研仪器需要注意什么？'
        ]
    else:
        with open(sample) as f:
            real_questions = json.load(f)

    for example in real_questions:
        relative, score = retriever.is_relative(example)

        if relative:
            logger.warning(f'process query: {example}')
        else:
            logger.error(f'reject query: {example}')

        if sample is not None:
            if relative:
                with open('workdir/positive.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
            else:
                with open('workdir/negative.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
    empty_cache()


def test_query(retriever: Retriever, sample: str = None):
    """Simple test response pipeline."""
    from texttable import Texttable
    if sample is not None:
        with open(sample) as f:
            real_questions = json.load(f)
        logger.add('logs/feature_store_query.log', rotation='4MB')
    else:
        real_questions = ['百草园里有啥？', 'how to use std::vector ?']

    table = Texttable()
    table.set_cols_valign(['t', 't', 't', 't'])
    table.header(['Query', 'State', 'Chunks', 'References'])

    for example in real_questions:
        example = example[0:400]
        chunks, context, refs, context_texts = retriever.query(example)
        if chunks:
            table.add_row(
                [example, 'Accepted', chunks[0:100] + '..', ','.join(refs)])
        else:
            table.add_row([example, 'Rejected', 'None', 'None'])
        empty_cache()

    logger.info('\n' + table.draw())
    empty_cache()


if __name__ == '__main__':
    args = parse_args()
    cache = CacheRetriever(config_path=args.config_path)
    fs_init = FeatureStore(embedder=cache.embedder,
                           config_path=args.config_path,
                           override=args.override)

    # walk all files in repo dir
    file_opr = FileOperation()

    files = file_opr.scan_dir(repo_dir=args.repo_dir)
    
    # Create configuration object
    init_config = InitializeConfig(
        files=files,
        work_dir=args.work_dir,
        ner_file=args.ner_file,
        qa_pair_file=args.qa_pair
    )

    fs_init.initialize(config=init_config)
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