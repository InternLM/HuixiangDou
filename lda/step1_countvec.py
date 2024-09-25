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
import jieba.posseg as jp
import json
import re
from multiprocessing import Process, cpu_count
# https://blog.csdn.net/xyisv/article/details/104482818

n_features = 2048
n_components = 20
n_top_words = 20
batch_size = 128

def files():
    basedir = '/home/data/khj/workspace/huixiangdou/lda/preprocess'

    docs = []
    for root, _, files in os.walk(basedir):
        for file in files:
            if file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg'):
                pdb.set_trace()
            else:
                docs.append((file, os.path.join(root, file)))
    return docs

def filecontents(dirname:str):
    filepaths = files()
    for _, filepath in filepaths:
        with open(filepath) as f:
            content = f.read()
            if len(content) > 0:
                yield content

# reference step https://blog.csdn.net/xyisv/article/details/104482818
def plot_top_words(model, feature_names, n_top_words, title):
    fig, axes = plt.subplots(2, 5, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[-n_top_words:]
        top_features = feature_names[top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f"Topic {topic_idx +1}", fontdict={"fontsize": 30})
        ax.tick_params(axis="both", which="major", labelsize=20)
        for i in "top right left".split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
    plt.savefig('topic_centers.jpg')

def build_topic(dirname: str='preprocess'):
    tf_vectorizer = CountVectorizer(
        max_df=0.95, min_df=2, max_features=n_features, stop_words="english"
    )

    t0 = time()
    tf = tf_vectorizer.fit_transform(filecontents(dirname))
    print("BoW in %0.3fs." % (time() - t0))

    lda = LatentDirichletAllocation(
        n_components=n_components,
        max_iter=5,
        learning_method="online",
        learning_offset=50.0,
        random_state=0,
    )
    t0 = time()
    lda.fit_transform(tf)
    print("lda train in %0.3fs." % (time() - t0))
    # transform(raw_documents)[source]
    feature_names = tf_vectorizer.get_feature_names_out()

    for topic_idx, topic in enumerate(lda.components_):
        top_features_ind = topic.argsort()[-n_top_words:]
        top_features = feature_names[top_features_ind]
        weights = topic[top_features_ind]
        print(top_features)

    import pdb
    pdb.set_trace()
    pass

if __name__ == '__main__':
    build_topic()
