from huixiangdou.primitive import Chunk, Query


def test_chunk():
    c = Chunk()
    c_str = '{}'.format(c)
    assert 'content_or_path=' in c_str


def test_query():
    q = Query(text='hello', image='test.jpg')
    q_str = '{}'.format(q)
    assert 'hello' in q_str
    assert 'image=' in q_str

    p = Query('hello')
    p_str = '{}'.format(p)
    assert 'text=' in p_str


if __name__ == '__main__':
    test_chunk()
    test_query()
