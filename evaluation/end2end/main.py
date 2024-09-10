from huixiangdou.service import ParallelPipeline, start_llm_server
from huixiangdou.primitive import Query
import json
import asyncio
import pdb
from typing import List
from rouge import Rouge 
from loguru import logger

assistant = ParallelPipeline(work_dir='/home/khj/hxd-ci/workdir', config_path='/home/khj/hxd-ci/config.ini')

def format_refs(refs: List[str]):
    refs_filter = list(set(refs))
    if len(refs) < 1:
        return ''

    text = '**References:**\r\n'
    for file_or_url in refs_filter:
        text += '* {}\r\n'.format(file_or_url)
    text += '\r\n'
    return text

async def run(query_text: str):
    query = Query(query_text)
    sentence = ''
    refs = None
    async for sess in assistant.generate(query=query, enable_web_search=False):
        if len(sess.delta) > 0:
            sentence += sess.delta
            if refs is None:
                refs = sess.references
    return sentence, refs

gts = []
dts = []

output_filepath = 'out.jsonl'

finished_query = []
with open(output_filepath) as fin:
    json_str = ""
    for line in fin:
        json_str += line
    
        if '}\n' == line:
            print(json_str)
            json_obj = json.loads(json_str)
            finished_query.append(json_obj['query'].strip())
            json_str = ""

with open('evaluation/end2end/qa.jsonl') as fin:
    for json_str in fin:
        json_obj = json.loads(json_str)
        query = json_obj['query'].strip()
        
        if query in finished_query:
            continue
        
        gt = json_obj['resp']
        gts.append(gt)

        loop = asyncio.get_event_loop()
        dt, refs = loop.run_until_complete(run(query_text=query))
        dts.append(dt)

        distance = assistant.retriever.embedder.distance(text1=gt, text2=dt).tolist()

        rouge = Rouge()
        scores = rouge.get_scores(gt, dt)
        json_obj['distance'] = distance
        json_obj['rouge_scores'] = scores
        json_obj['dt'] = dt
        json_obj['dt_refs'] = refs

        out_json_str = json.dumps(json_obj, ensure_ascii=False, indent=2)
        logger.info(out_json_str)

        with open(output_filepath, 'a') as fout:
            fout.write(out_json_str)
            fout.write('\n')
