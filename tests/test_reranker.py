import json
import os
import pdb

import numpy as np
import torch
from BCEmbedding import RerankerModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def get_inputs(pairs, tokenizer, prompt=None, max_length=1024):
    if prompt is None:
        prompt = "Given a query A and a passage B, determine whether the passage contains an answer to the query by providing a prediction of either 'Yes' or 'No'."
    sep = '\n'
    prompt_inputs = tokenizer(prompt,
                              return_tensors=None,
                              add_special_tokens=False)['input_ids']
    sep_inputs = tokenizer(sep, return_tensors=None,
                           add_special_tokens=False)['input_ids']
    inputs = []
    for query, passage in pairs:
        query_inputs = tokenizer(f'A: {query}',
                                 return_tensors=None,
                                 add_special_tokens=False,
                                 max_length=max_length * 3 // 4,
                                 truncation=True)
        passage_inputs = tokenizer(f'B: {passage}',
                                   return_tensors=None,
                                   add_special_tokens=False,
                                   max_length=max_length,
                                   truncation=True)
        item = tokenizer.prepare_for_model(
            [tokenizer.bos_token_id] + query_inputs['input_ids'],
            sep_inputs + passage_inputs['input_ids'],
            truncation='only_second',
            max_length=max_length,
            padding=False,
            return_attention_mask=False,
            return_token_type_ids=False,
            add_special_tokens=False)
        item['input_ids'] = item['input_ids'] + sep_inputs + prompt_inputs
        item['attention_mask'] = [1] * len(item['input_ids'])
        inputs.append(item)
    return tokenizer.pad(inputs,
                         padding=True,
                         max_length=max_length + len(sep_inputs) +
                         len(prompt_inputs),
                         pad_to_multiple_of=8,
                         return_tensors='pt')


def test_llm_reranker():
    model_path = '/data2/khj/bge-reranker-v2-minicpm-layerwise'
    tokenizer = AutoTokenizer.from_pretrained(model_path,
                                              trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path,
                                                 trust_remote_code=True,
                                                 torch_dtype=torch.bfloat16)
    model = model.to('cuda')
    model.eval()

    outdir = '/home/khj/hxd-ci/odir'
    with torch.no_grad():
        dirpath = '/home/khj/hxd-ci/candidates'
        for name in os.listdir(dirpath):
            fullpath = os.path.join(dirpath, name)
            outfullpath = os.path.join(outdir, name)

            with open(fullpath) as fin:
                for jsonstr in fin:
                    jsonobj = json.loads(jsonstr)
                    pairs = []
                    query = jsonobj['query']
                    candidates = jsonobj['candidates']

                    output = {'query': query, 'rank': []}
                    for can in candidates:
                        content = can['content']
                        pairs.append([query, content])

                    inputs = get_inputs(pairs, tokenizer).to(model.device)
                    all_scores = model(**inputs,
                                       return_dict=True,
                                       cutoff_layers=[28])
                    all_scores = [
                        scores[:, -1].view(-1, ).float()
                        for scores in all_scores[0]
                    ]
                    all_scores = all_scores[0].cpu().numpy()
                    # get descending order
                    indexes = all_scores.argsort()[::-1]
                    for index in indexes:
                        output['rank'].append(candidates[index]['content'])
                    outstr = json.dumps(output, ensure_ascii=False, indent=2)

                    with open(outfullpath, 'a') as fout:
                        fout.write(outstr)
                        fout.write('\n')


def test_bce_reranker():
    whitelist = [
        '0JOL.jsonl', '0ki5.jsonl', '0oDm.jsonl', '1lA9.jsonl', '2P8j.jsonl'
    ]
    model_path = '/data2/khj/bce-embedding-base_v1'
    model = RerankerModel(model_name_or_path=model_path)

    outdir = '/home/khj/hxd-ci/bceodir'
    with torch.no_grad():
        dirpath = '/home/khj/hxd-ci/candidates'
        for name in os.listdir(dirpath):
            if name not in whitelist:
                continue
            fullpath = os.path.join(dirpath, name)
            outfullpath = os.path.join(outdir, name)

            with open(fullpath) as fin:
                for jsonstr in fin:
                    jsonobj = json.loads(jsonstr)
                    pairs = []
                    query = jsonobj['query']
                    passages = []
                    candidates = jsonobj['candidates']

                    output = {'query': query, 'rank': []}
                    for can in candidates:
                        content = can['content']
                        passages.append(content)

                    rerank_results = model.rerank(query, passages)
                    output['rank'] = rerank_results['rerank_passages']

                    outstr = json.dumps(output, ensure_ascii=False, indent=2)
                    with open(outfullpath, 'a') as fout:
                        fout.write(outstr)
                        fout.write('\n')


# test_bce_reranker()
test_llm_reranker()
