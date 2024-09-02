# from .splitter import CharacterTextSplitter, ChineseRecursiveTextSplitter, RecursiveCharacterTextSplitter, MarkdownTextRefSplitter, MarkdownHeaderTextSplitter  # noqa E401
import pdb

from huixiangdou.primitive import (CharacterTextSplitter,
                                   ChineseRecursiveTextSplitter,
                                   MarkdownHeaderTextSplitter,
                                   MarkdownTextRefSplitter,
                                   RecursiveCharacterTextSplitter,
                                   nested_split_markdown, split_python_code)


def test_character_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = CharacterTextSplitter()
    print(type(s))
    splits = s.split_text(text)
    assert len(splits) > 10

    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/character_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('-----------\n')
    return chunks


def test_recursive_character_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = RecursiveCharacterTextSplitter()
    print(type(s))
    splits = s.split_text(text)

    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/recursive_character_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks


def test_chinese_recursive_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = ChineseRecursiveTextSplitter()
    print(type(s))
    splits = s.split_text(text)

    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/chinese_recursive_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks


def test_markdown_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = MarkdownTextRefSplitter()
    print(type(s))
    splits = s.split_text(text)

    chunks = s.create_chunks([text], [{'path': path}])
    assert len(chunks) == len(splits)
    with open('/tmp/markdown_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks


def test_markdown_header_text_splitter():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    s = MarkdownHeaderTextSplitter()
    print(type(s))
    chunks = s.create_chunks(text, metadata={'path': path})
    with open('/tmp/markdown_header_text_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks


def test_nested_markdown_split():
    path = 'README_zh.md'
    with open(path) as f:
        text = f.read()
    print(type('nested'))

    chunks = nested_split_markdown(filepath=path, text=text, chunksize=768)
    with open('/tmp/markdown_nested_split', 'w') as f:
        for c in chunks:
            print(len(c.content_or_path))
            f.write(c.content_or_path)
            f.write('\n-----------\n')
    return chunks

def test_split_python_code():
    path = "huixiangdou/main.py"
    with open(path) as f:
        content = f.read()
    
    chunks = split_python_code(filepath=path, text=content, metadata={"test": "meta"})
    for chunk in chunks:
        print(chunk)

if __name__ == '__main__':
    test_split_python_code()
    # test_character_text_splitter()
    # test_recursive_character_text_splitter()
    # test_chinese_recursive_text_splitter()
    # test_markdown_text_splitter()
    # test_markdown_header_text_splitter()
    # test_nested_markdown_split()
