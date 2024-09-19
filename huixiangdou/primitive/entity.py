import sqlite3
import os
import json
from typing import List, Union, Set

class NamedEntity2Chunk:
    """Save the relationship between Named Entity and Chunk to sqlite"""
    def __init__(self, file_dir:str, ignore_case=True):
        self.file_dir = file_dir
        # case sensitive
        self.ignore_case = ignore_case
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        self.conn = sqlite3.connect(os.path.join(file_dir, 'entity2chunk.sql'))
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            eid INTEGER PRIMARY KEY,
            chunk_ids TEXT
        )
        ''')
        self.conn.commit()
        self.entities = []
        self.entity_path = os.path.join(self.file_dir, 'entities.json') 
        if os.path.exists(self.entity_path):
            with open(self.entity_path) as f:
                self.entities = json.load(f)
                if self.ignore_case:
                    for id, value in enumerate(self.entities):
                        self.entities[id] = value.lower()

    def clean(self):
        self.cursor.execute('''DROP TABLE entities;''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            eid INTEGER PRIMARY KEY,
            chunk_ids TEXT
        )
        ''')
        self.conn.commit()

    def insert_relation(self, eid: int, chunk_ids: List[int]):
        """Insert the relationship between keywords id and List of chunk_id"""
        chunk_ids_str = ','.join(map(str, chunk_ids)) 
        self.cursor.execute('INSERT INTO entities (eid, chunk_ids) VALUES (?, ?)', (eid, chunk_ids_str))
        self.conn.commit()
    
    def parse(self, text:str) -> List[int]:
        if self.ignore_case:
            text = text.lower()
        
        if len(self.entities) < 1:
            raise ValueError('entity list empty, please check feature_store init')
        ret = []
        for index, entity in enumerate(self.entities):
            if entity in text:
                ret.append(index)
        return ret

    def set_entity(self, entities: List[str]):
        json_str = json.dumps(entities, ensure_ascii=False)
        with open(self.entity_path, 'w') as f:
            f.write(json_str)
            
        self.entities = entities
        if self.ignore_case:
            for id, value in enumerate(self.entities):
                self.entities[id] = value.lower()

    def get_chunk_ids(self, entity_ids: Union[List, int]) -> Set:
        """Query by keywords ids"""
        if type(entity_ids) is int:
            entity_ids = [entity_ids]
        
        counter = dict()
        for eid in entity_ids:
            self.cursor.execute('SELECT chunk_ids FROM entities WHERE eid = ?', (eid,))
            result = self.cursor.fetchone()
            if result:
                chunk_ids = result[0].split(',')
                for chunk_id_str in chunk_ids:
                    chunk_id = int(chunk_id_str)
                    if chunk_id not in counter:
                        counter[chunk_id] = 1
                    else:
                        counter[chunk_id] += 1
        
        counter_list = []
        for k,v in counter.items():
            counter_list.append((k,v))
        counter_list.sort(key=lambda item: item[1], reverse=True)
        return counter_list
    
    def __del__(self):
        self.cursor.close()
        self.conn.close()
