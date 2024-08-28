# Useful debug code, TL;DR.

def langchain_splitter(text: str, chunk_size:int, metadata):
    """This is for debugging"""
    from langchain.text_splitter import MarkdownTextSplitter
    md_splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=32)
    docs = md_splitter.create_documents([text])
    
    chunks = []
    for doc in docs:
        c = Chunk(content_or_path=doc.page_content, metadata=metadata)
        chunks.append(c)
    return chunks

# compare splitter
if False:
    # Here is for splitter result comparison, useless
    gt_chunks = langchain_splitter(chunk.content_or_path, chunksize, chunk.metadata)
    if len(subchunks) != len(gt_chunks):
        pdb.set_trace()
        pass
    for ii in range(len(subchunks)):
        if subchunks[ii].content_or_path != gt_chunks[ii].content_or_path:
            pdb.set_trace()

from langchain.text_splitter import MarkdownHeaderTextSplitter as LangChainMarkdownHeaderTextSplitter
gt_head_splitter = LangChainMarkdownHeaderTextSplitter(headers_to_split_on=[
        ('#', 'Header 1'),
        ('##', 'Header 2'),
        ('###', 'Header 3'),
    ])
docs = gt_head_splitter.split_text(text)
if len(docs) != len(chunks):
    pdb.set_trace()
    print('len diff')
for idx in range(len(docs)):
    doc = docs[idx]
    chunk = chunks[idx]
    if doc.page_content != chunk.content_or_path:
        pdb.set_trace()
        print('content diff')

with open('headersplit.result', 'a') as f:
    for chunk in chunks:

        header = ''
        if len(chunk.metadata) > 0:
            if 'Header 1' in chunk.metadata:
                header += chunk.metadata['Header 1']
            if 'Header 2' in chunk.metadata:
                header += ' '
                header += chunk.metadata['Header 2']
            if 'Header 3' in chunk.metadata:
                header += ' '
                header += chunk.metadata['Header 3']

        json_str = json.dumps({'data': header + ' ||| ' + chunk.content_or_path}, ensure_ascii=False)
        f.write(json_str)
        f.write('\n')

with open('refactor.json', 'w') as f:
    pass

with open('refactor.jsonl', 'a') as f:
    for c in text_chunks:
        json_str = json.dumps({'data': c.content_or_path}, ensure_ascii=False)
        f.write(json_str)
        f.write('\n')