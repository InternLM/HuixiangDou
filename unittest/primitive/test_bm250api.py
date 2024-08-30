from huixiangdou.primitive import BM25Okapi, Chunk
import pdb

def test_bm25_dump():
    corpus = [
        "Hello there good man!",
        "It is quite windy in London",
        "How is the weather today?"
    ]
    chunks = []
    for content in corpus:
        c = Chunk(content_or_path=content)
        chunks.append(c)

    bm25 = BM25Okapi()
    pdb.set_trace()
    bm25.save(chunks, 'bm25.pkl')

def test_bm25_load():
    bm25 = BM25Okapi()
    pdb.set_trace()
    bm25.load('bm25.pkl')

if __name__ == '__main__':
    test_bm25_dump()
    test_bm25_load()
