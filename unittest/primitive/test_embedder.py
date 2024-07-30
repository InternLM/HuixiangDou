from huixiangdou.primitive import Embedder
import pdb

def test_embedder():
    assert Embedder.use_multimodal(model_path='/data2/khj/bge-m3') is True

    emb = Embedder(model_path='/data2/khj/bge-m3')
    sentence = 'hello world '
    sentence_16k = sentence * (16384 // len(sentence))
    image_path = 'resource/figures/wechat.jpg'
    
    text_feature = emb.embed_query(text=sentence_16k)
    image_feature = emb.embed_query(path=image_path)

    query_feature = emb.embed_query(text=sentence_16k, path=image_path)

    sim1 = query_feature @ text_feature.T
    sim2 = query_feature @ image_feature.T

    assert sim1.item() >= 0.5
    assert sim2.item() >= 0.5

if __name__ == '__main__':
    test_embedder()
