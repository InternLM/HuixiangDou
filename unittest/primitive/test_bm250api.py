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
    bm25.save(chunks, './')

def test_bm25_load():
    bm25 = BM25Okapi()
    bm25.load('./')
    query_text = 'what is the weather'
    
    res = bm25.get_top_n(query=query_text.split(' '))
    print(res)

    res = bm25.get_top_n(query=query_text)
    print(res)

if __name__ == '__main__':
    test_bm25_dump()
    test_bm25_load()
