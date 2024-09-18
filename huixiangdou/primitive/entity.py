import sqlite3
import os
import json
from typing import List, Union, Set

class NamedEntity2Chunk:
    """Save the relationship between Named Entity and Chunk to sqlite"""
    def __init__(self, file_dir:str):
        self.file_dir = file_dir
        self.conn = sqlite3.connect(os.path.join(file_dir, 'entity2chunk.sql'))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            kid INTEGER PRIMARY KEY,
            chunk_ids TEXT
        )
        ''')
        self.conn.commit()
        
        self.entities = []
        self.entity_path = os.path.join(self.file_dir, 'entities.json') 
        if os.path.exists(self.entity_path):
            with open(self.entity_path) as f:
                self.entities = json.load(f)

    def insert_relation(self, kid: int, chunk_ids: List[int]):
        """Insert the relationship between keywords id and List of chunk_id"""
        chunk_ids_str = ','.join(map(str, chunk_ids))  # 将列表转换为字符串
        self.cursor.execute('INSERT INTO entities (kid, chunk_ids) VALUES (?, ?)', (kid, chunk_ids_str))
        self.conn.commit()
        
    def parse(self, text:str) -> List[int]:
        if len(self.entities) < 1:
            raise ValueError('entity list empty, please check feature_store init')
        ret = []
        for index, entity in self.entities:
            if entity in text:
                ret.append(index)
        return ret

    def set_entity(self, entities: List[str]):
        json_str = json.dumps(entities, ensure_ascii=False)
        with open(self.entity_path, 'w') as f:
            f.write(json_str)
        self.entities = entities

    def get_chunk_ids(self, kids: Union[List, int]) -> Set:
        """Query by keywords ids"""
        if type(kids) is int:
            kids = [kids]
        
        rets = set()
        for kid in kids:
            self.cursor.execute('SELECT chunk_ids FROM entities WHERE kid = ?', (kid,))
            result = self.cursor.fetchone()
            if result:
                ids = set(result[0].split(','))
                rets.update(ids)
        return rets
    
    def __del__(self):
        self.cursor.close()
        self.conn.close()
