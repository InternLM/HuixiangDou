import jieba
import jieba.posseg as jp
import json

def load_newwords():
    words = []
    with open('ner.json', encoding='utf8') as f:
        words = json.load(f)
    return words

# add newwords
def init_jieba():
    new_words = load_newwords()
    for w in new_words:
        jieba.add_word(w)
