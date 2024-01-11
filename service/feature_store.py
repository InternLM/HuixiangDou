import re
from pathlib import Path
import os
from loguru import logger
import numpy as np
import sentence_transformers
from loguru import logger
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import MarkdownTextSplitter, MarkdownHeaderTextSplitter, CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS as Vectorstore
from sklearn.metrics import precision_recall_curve
import pytoml
import json
import shutil
import numpy as np
import argparse
import pdb


class FeatureStore(object):

    def __init__(self,
                 device: str = "cuda",
                 config_path: str = "config.ini") -> None:

        self.config_path = config_path
        self.reject_throttle = -1
        with open(config_path) as f:
            config = pytoml.load(f)['feature_store']
            model_path = config['model_path']
            self.reject_throttle = config['reject_throttle']

        if model_path is None or len(model_path) == 0:
            raise Exception(f'model_path can not be empty')

        self.embeddings = HuggingFaceEmbeddings(model_name='')
        self.embeddings.client = sentence_transformers.SentenceTransformer(
            model_path, device=device)
        self.vector_store_reject = None
        self.vector_store_db = None

        self.md_splitter = MarkdownTextSplitter(chunk_size=768,
                                                chunk_overlap=32)
        self.text_splitter = CharacterTextSplitter(chunk_size=768)

        self.head_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ])

    def contains_chinese(self, text):
        if re.search('[\u4e00-\u9fff]', text):
            return True
        else:
            return False

    def is_chinese_doc(self, text):
        chinese_characters = re.findall(r'[\u4e00-\u9fff]', text)
        total_characters = len(text)
        ratio = 0
        if total_characters > 0:
            ratio = len(chinese_characters) / total_characters
        if ratio >= 0.005:
            return True
        return False

    def cos_similarity(self, v1: list, v2: list):
        num = float(np.dot(v1, v2))
        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        return 0.5 + 0.5 * (num / denom) if denom != 0 else 0

    def distance(self, text1: str, text2: str):
        feature1 = self.embeddings.embed_query(text1)
        feature2 = self.embeddings.embed_query(text2)
        return self.cos_similarity(feature1, feature2)

    def split_md(self, text: str, source: None):
        docs = self.head_splitter.split_text(text)

        final = []
        for doc in docs:
            header = ''
            if len(doc.metadata) > 0:
                if 'Header 1' in doc.metadata:
                    header += doc.metadata['Header 1']
                if 'Header 2' in doc.metadata:
                    header += ' '
                    header += doc.metadata['Header 2']
                if 'Header 3' in doc.metadata:
                    header += ' '
                    header += doc.metadata['Header 3']

            if len(doc.page_content) >= 1024:
                subdocs = self.md_splitter.create_documents([doc.page_content])
                for subdoc in subdocs:
                    if len(subdoc.page_content) >= 10:
                        final.append('{} {}'.format(
                            header, subdoc.page_content.lower()))
            elif len(doc.page_content) >= 10:
                final.append('{} {}'.format(header, doc.page_content.lower()))

        for item in final:
            if len(item) >= 1024:
                logger.debug('source {} split length {}'.format(
                    source, len(item)))
        return final

    def clean_md(self, text: str):
        # remove ref
        pattern_ref = r'\[(.*?)\]\(.*?\)'
        new_text = re.sub(pattern_ref, r'\1', text)

        # remove code block
        pattern_code = r'```.*?```'
        new_text = re.sub(pattern_code, '', new_text, flags=re.DOTALL)

        # remove underline
        new_text = re.sub('_{5,}', '', new_text)

        # remove table
        # new_text = re.sub('\|.*?\|\n\| *\:.*\: *\|.*\n(\|.*\|.*\n)*', '', new_text, flags=re.DOTALL)

        # use lower
        new_text = new_text.lower()
        return new_text

    def ingress_response(self, markdown_dir: str, work_dir: str):
        feature_dir = os.path.join(work_dir, "db_response")
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)

        ps = list(Path(markdown_dir).glob("**/*.md"))

        full_texts = []
        sources = []
        for p in ps:

            with open(p) as f:
                full_text = str(p).split('/_')[-1] + '\n' + f.read()
                if '.md' in str(p):
                    if not self.is_chinese_doc(full_text):
                        continue

                full_texts.append(full_text)
                sources.append(str(p))

        shadows = []
        metadatas = []

        # source: 文件路径
        # full_texts: 完整的文本，没做任何处理
        # text: 清理 markdown 后的内容
        # splits: 清理 markdown，然后划分文本
        for i, text in enumerate(full_texts):
            logger.debug('{}/{}..'.format(i, len(full_texts)))

            text = self.clean_md(text)
            splits = self.split_md(text=text, source=sources[i])
            shadows.extend(splits)

            for split in splits:
                metadatas.append({"source": sources[i], "data": split})

        vs = Vectorstore.from_texts(shadows,
                                    self.embeddings,
                                    metadatas=metadatas)
        vs.save_local(feature_dir)

    def ingress_reject(self, markdown_dir: str, work_dir: str):
        feature_dir = os.path.join(work_dir, "db_reject")
        if not os.path.exists(feature_dir):
            os.makedirs(feature_dir)

        ps = list(Path(markdown_dir).glob("**/*.md"))
        data = []
        sources = []
        for p in ps:
            with open(p) as f:
                data.append(f.read())
            sources.append(p)

        docs = []
        metadatas = []
        for i, d in enumerate(data):
            logger.debug('{}/{}..'.format(i, len(data)))
            splits = self.split_md(text=d, source=sources[i])

            docs.extend(splits)
            if len(docs) > 0:
                metadatas.extend([{"source": sources[i]}] * len(splits))

        vs = Vectorstore.from_texts(docs, self.embeddings, metadatas=metadatas)
        vs.save_local(feature_dir)

    def load_feature(self,
                     work_dir,
                     feature_response: str = "db_response",
                     feature_reject: str = 'db_reject'):
        # https://api.python.langchain.com/en/latest/vectorstores/langchain.vectorstores.faiss.FAISS.html#langchain.vectorstores.faiss.FAISS
        self.vector_store_reject = Vectorstore.load_local(
            os.path.join(work_dir, feature_response),
            embeddings=self.embeddings)
        self.vector_store_db = Vectorstore.load_local(
            os.path.join(work_dir, feature_reject), embeddings=self.embeddings)

    def get_doc_by_id(self, _id, vector_store):
        return vector_store.docstore.search(
            vector_store.index_to_docstore_id[_id])

    def process_strings(self, A, C, B):
        # find the longest common suffix of A and prefix of B
        common = ""
        for i in range(1, min(len(A), len(B)) + 1):
            if A[-i:] == B[:i]:
                common = A[-i:]
        # if there is a common substring, replace one of them with C and concatenate
        if common:
            return A[:-len(common)] + C + B
        # otherwise, just return A + B
        else:
            return A + B

    def get_doc(self, id, score, step, vector_store):
        doc = self.get_doc_by_id(id, vector_store=vector_store)
        final_content = doc.page_content
        if step > 0:
            for i in range(1, step + 1):
                try:
                    doc_before = self.get_doc_by_id(id - i,
                                                    vectore_store=vector_store)
                    if doc_after.metadata['source'] == doc.metadata['source']:
                        final_content = self.process_strings(
                            doc_before.page_content, '\n', final_content)
                except:
                    pass
                try:
                    doc_after = self.get_doc_by_id(id + i,
                                                   vectore_store=vector_store)
                    if doc_after.metadata['source'] == doc.metadata['source']:
                        final_content = self.process_strings(
                            final_content, '\n', doc_after.page_content)
                except:
                    pass
        source = str(doc.metadata['source'])

        if 'data' in doc.metadata:
            data = str(doc.metadata['data'])
        else:
            data = None
        if source.endswith(".pdf") or source.endswith(".txt"):
            path = f"[{doc.metadata['source']}](/txt/{doc.metadata['source']})"
        else:
            path = source
        return {
            'path': path,
            'content': re.sub(r'\n+', "\n", final_content),
            "score": int(score),
            "data": data
        }

    def _search(self, question: str, vector_store, topk: int = 3, throttle=-1):
        try:
            embedding = vector_store.embedding_function(question)
            scores, indices = vector_store.index.search(
                np.array([embedding], dtype=np.float32), topk)
            docs = []
            for j, i in enumerate(indices[0]):
                if i == -1:
                    continue
                # print(question, scores[0][j], throttle)
                if throttle >= 0 and scores[0][j] >= throttle:
                    # print(question, scores[0][j])
                    continue
                docs.append(
                    self.get_doc(i, scores[0][j], 0,
                                 vector_store=vector_store))

            return docs
        except Exception as e:
            logger.error('{}'.format(__file__, str(e)))
            # pdb.set_trace()
            return []

    def db_search(self, question):
        docs = self._search(question=question,
                            vector_store=self.vector_store_db,
                            topk=1,
                            throttle=-1)
        return docs, []

    def is_reject(self, question):
        docs = self._search(question=question,
                            vector_store=self.vector_store_reject,
                            topk=1,
                            throttle=self.reject_throttle)
        if len(docs) < 1:
            return True
        return False

    def query(self, question: str):
        if len(question) < 1 or self.is_reject(question=question):
            return '<reject>'

        docs, keyword_set = self.db_search(question=question.lower())
        for doc in docs:
            logger.debug(('db', doc['score'], question))
        ret = [doc['data'] for doc in docs]
        logger.debug('query:{} keyword_set:{} ret:{}'.format(
            question, keyword_set, ret))
        return ' '.join(ret)

    def query_source(self, question: str):
        if len(question) < 1 or self.is_reject(question=question):
            return '<reject>', '<reject>'

        docs, _ = self.db_search(question=question.lower())
        doc = docs[0]
        path = doc['path']
        part = doc['content']
        full = ''
        with open(path) as f:
            full = f.read()
        return part, full

    def preprocess(self, repo_dir: str, work_dir: str):
        markdown_dir = os.path.join(work_dir, 'preprocess')
        if os.path.exists(markdown_dir):
            logger.warning(f'{markdown_dir} already exists, remove and regenerate.')
            shutil.rmtree(markdown_dir)
        os.makedirs(markdown_dir)

        # find all .md files except those containing mdb
        mds = []
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.endswith('.md') and 'mdb' not in file:
                    mds.append(os.path.join(root, file))

        if len(mds) < 1:
            raise Exception(f'cannot search any markdown file, please check usage: python3 {__file__} workdir repodir')
        # copy each file to ./finetune-data/ with new name
        for _file in mds:
            tmp = _file.replace("/", "_")
            name = tmp[1:] if tmp.startswith(".") else tmp
            logger.info(name)
            shutil.copy(_file, f'{markdown_dir}/{name}')
        logger.debug(f'preprcessed {len(mds)} files.')
        return markdown_dir

    def initialize(self,
                   repo_dir: str,
                   work_dir: str,
                   config_path: str = 'config.ini',
                   good_questions=[],
                   bad_questions=[]):
        logger.info(
            'initialize response and reject feature store, you only need call this once.'
        )
        self.reject_throttle = -1
        markdown_dir = self.preprocess(repo_dir=repo_dir, work_dir=work_dir)
        self.ingress_response(markdown_dir=markdown_dir, work_dir=work_dir)
        self.ingress_reject(markdown_dir=markdown_dir, work_dir=work_dir)

        if len(good_questions) == 0 or len(bad_questions) == 0:
            raise Exception(
                f'good and bad question examples cat not be empty.')
        self.load_feature(work_dir=work_dir)
        questions = good_questions + bad_questions
        predictions = []
        for question in questions:
            docs = self._search(question=question,
                                vector_store=self.vector_store_reject,
                                topk=1)
            score = docs[0]['score']
            predictions.append(1e6 - score)

        labels = [1 for _ in range(len(good_questions))
                  ] + [0 for _ in range(len(bad_questions))]
        precision, recall, thresholds = precision_recall_curve(
            labels, predictions)

        # get the best index for sum(precison, recall)
        sum_precision_recall = precision[:-1] + recall[:-1]
        index_max = np.argmax(sum_precision_recall)
        optimal_threshold = 1e6 - thresholds[index_max]

        with open(config_path, 'r') as f:
            config = pytoml.load(f)
        config['feature_store']['reject_throttle'] = optimal_threshold
        with open(config_path, 'w') as f:
            pytoml.dump(config, f)

        logger.info(
            f"The optimal threshold is: {optimal_threshold}, saved it to {config_path}"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description='Feature store for processing directories.')
    parser.add_argument('--work_dir', type=str, default='workdir', help='Working directory.')
    parser.add_argument(
        '--repo_dir',
        type=str,
        default='repodir',
        help='Root directory where the repositories are located.')
    parser.add_argument(
        '--good_questions',
        default='resource/good_questions.json',
        help=
        'The json file path of positive examples in the dataset. Default value is resource/good_questions.json'
    )
    parser.add_argument(
        '--bad_questions',
        default='resource/bad_questions.json',
        help=
        'The json file path of negative examples. Default value is resource/bad_questions.json'
    )
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Feature store configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args


def test_reject():
    real_questions = [
        '请问找不到libmmdeploy.so怎么办', 'SAM 10个T 的训练集，怎么比比较公平呢~？速度上还有缺陷吧？',
        '想问下，如果只是推理的话，amp的fp16是不会省显存么，我看parameter仍然是float32，开和不开推理的显存占用都是一样的。能不能直接用把数据和model都 .half() 代替呢，相比之下amp好在哪里',
        'mmdeploy支持ncnn vulkan部署么，我只找到了ncnn cpu 版本',
        '大佬们，如果我想在高空检测安全帽，我应该用 mmdetection 还是 mmrotate',
        'mmdeploy 现在支持 mmtrack 模型转换了么', '请问 ncnn 全称是什么',
        '有啥中文的 text to speech 模型吗?', '今天中午吃什么？', '茴香豆是怎么做的'
    ]
    fs_query = FeatureStore(config_path=args.config_path)
    fs_query.load_feature(work_dir=args.work_dir)
    for example in real_questions:
        if fs_query.is_reject(example):
            logger.error(f'reject query: {example}')
        else:
            logger.warning(f'process query: {example}')
    del fs_query

def test_query():
    real_questions = [
        '视频流检测'
    ]
    fs_query = FeatureStore(config_path=args.config_path)
    fs_query.load_feature(work_dir=args.work_dir)
    for example in real_questions:
        print(fs_query.query_source(example))
    del fs_query

if __name__ == '__main__':
    args = parse_args()
    fs_init = FeatureStore(config_path=args.config_path)
    with open(args.good_questions) as f:
        good_questions = json.load(f)
    with open(args.bad_questions) as f:
        bad_questions = json.load(f)

    fs_init.initialize(repo_dir=args.repo_dir,
                       work_dir=args.work_dir,
                       good_questions=good_questions,
                       bad_questions=bad_questions)
    del fs_init

    test_query()
    test_reject()
