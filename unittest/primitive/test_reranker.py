import pdb

from huixiangdou.primitive import LLMReranker


def test_reranker():
    model = LLMReranker({'reranker_model_path':'/data2/khj/bce-reranker-base_v1'})

    query = 'apple'
    texts = [ 'roast banana', 'ice juice', 'red orange', 'apple pie']
    scores = model._sort(texts=texts, query=query)

    assert scores[0] == len(texts) - 1


if __name__ == '__main__':
    test_reranker()
