# Author: Olivier Grisel <olivier.grisel@ensta.org>
#         Lars Buitinck
#         Chyi-Kwei Yau <chyikwei.yau@gmail.com>
# License: BSD 3 clause

from time import time

import matplotlib.pyplot as plt
import pdb
import os

from sklearn.datasets import fetch_20newsgroups
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
import jieba
import json
import pdb

n_samples = 2000
n_features = 1000
n_components = 10
n_top_words = 20
batch_size = 128

def file_contents():
    basedir = 'preprocess'
    files = os.listdir(basedir)
    for file in files:
        filepath = os.path.join(basedir, file)
        with open(filepath) as f:
            content = f.read()
            if len(content) > 0:
                yield content

xx = file_contents()
for item in xx:
    print(len(item))

tf_vectorizer = CountVectorizer(
    max_df=0.95, min_df=2, max_features=n_features, stop_words="english"
)

tf_vectorizer.fit_transform(file_contents())
pdb.set_trace()
