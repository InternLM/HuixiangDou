from huixiangdou.primitive import BM25Okapi

def test_bm25():
    corpus = [
        "Hello there good man!",
        "It is quite windy in London",
        "How is the weather today?"
    ]
    bm25 = BM25Okapi()
    tokenized_corpus = [doc.split(" ") for doc in corpus]
    bm25.save(tokenized_corpus, 'bm25.pkl')

if __name__ == '__main__':
    test_bm25()
