import os
import pdb

from huixiangdou.primitive import NamedEntity2Chunk, Chunk


def test_entity_build_and_query():
    entities = ['HuixiangDou', 'WeChat']
    
    indexer = NamedEntity2Chunk('/tmp')
    indexer.clean()
    indexer.set_entity(entities=entities)

    c0 = Chunk(content_or_path='How to deploy HuixiangDou on wechaty ?')
    c1 = Chunk(content_or_path='do you know what huixiangdou means ?')
    chunks = [c0, c1]
    map_entity2chunks = dict()
    # build inverted index
    for chunk_id, chunk in enumerate(chunks):
        if chunk.modal != 'text':
            continue
        entity_ids = indexer.parse(text=chunk.content_or_path)
        for entity_id in entity_ids:
            if entity_id not in map_entity2chunks:
                map_entity2chunks[entity_id] = [chunk_id]
            else:
                map_entity2chunks[entity_id].append(chunk_id)

    for entity_id, chunk_indexes in map_entity2chunks.items():
        indexer.insert_relation(eid = entity_id, chunk_ids=chunk_indexes)
    del indexer
    
    query_text = 'how to install wechat ?'
    retriver = NamedEntity2Chunk('/tmp')
    entity_ids = retriver.parse(query_text)
    # chunk_id match counter
    chunk_id_list = retriver.get_chunk_ids(entity_ids=entity_ids)
    print(chunk_id_list)
    assert chunk_id_list[0][0] == 0


if __name__ == '__main__':
    test_entity_build_and_query()
