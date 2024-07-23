from huixiangdou.primitive import Chunk

def test_chunk():
    c = Chunk()
    c_str = '{}'.format(c)
    assert 'content_or_path=' in c_str

if __name__ == '__main__':
    test_chunk()
