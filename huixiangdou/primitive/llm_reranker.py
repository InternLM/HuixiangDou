# Copyright (c) OpenMMLab. All rights reserved.
import json
import os
import pdb
from typing import List

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .embedder import Embedder

# else:
#     logger.warning(
#         'For higher rerank precision, we strong advice using `BAAI/bge-reranker-v2-minicpm-layerwise`'
#     )
#     reranker_args = {
#         'model': reranker_model_path,
#         'top_n': rerank_topn,
#         'device': 'cuda',
#         'use_fp16': True
#     }
#     self.reranker = BCERerank(**reranker_args)

class LLMReranker:

    def __init__(
            self,
            model_name_or_path: str = 'BAAI/bge-reranker-v2-minicpm-layerwise',
            topn: int = 10):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path,
                                                       trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16).eval()
        self.model = self.model.to('cuda')
        self.topn = topn

    def use_llm_reranker(self, model_path):
        """Check reranker model is LLM reranker or not."""

        config_path = os.path.join(model_path, 'config.json')
        if not os.path.exists(config_path):
            if 'bge-reranker-v2-minicpm-layerwise' in config_path.lower():
                return True
            return False
        try:
            with open(config_path) as f:
                if 'bge-reranker-v2-minicpm-layerwise' in json.loads(
                        f.read())['_name_or_path']:
                    return True
        except Exception as e:
            logger.warning(e)
        return False

    def get_inputs(self, pairs, prompt=None, max_length=1024):
        """Build input tokens with query and chunks."""
        if prompt is None:
            prompt = "Given a query A and a passage B, determine whether the passage contains an answer to the query by providing a prediction of either 'Yes' or 'No'."
        sep = '\n'
        prompt_inputs = self.tokenizer(prompt,
                                       return_tensors=None,
                                       add_special_tokens=False)['input_ids']
        sep_inputs = self.tokenizer(sep,
                                    return_tensors=None,
                                    add_special_tokens=False)['input_ids']
        inputs = []
        for query, passage in pairs:
            query_inputs = self.tokenizer(f'A: {query}',
                                          return_tensors=None,
                                          add_special_tokens=False,
                                          max_length=max_length * 3 // 4,
                                          truncation=True)
            passage_inputs = self.tokenizer(f'B: {passage}',
                                            return_tensors=None,
                                            add_special_tokens=False,
                                            max_length=max_length,
                                            truncation=True)
            item = self.tokenizer.prepare_for_model(
                [self.tokenizer.bos_token_id] + query_inputs['input_ids'],
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
        return self.tokenizer.pad(inputs,
                                  padding=True,
                                  max_length=max_length + len(sep_inputs) +
                                  len(prompt_inputs),
                                  pad_to_multiple_of=8,
                                  return_tensors='pt')

    def sort(self, chunks: List[str], query: str):
        """Rerank input chunks, return descending indexes, indexes[0] is the
        nearest chunk."""
        pairs = []
        for chunk in chunks:
            pairs.append([query, chunk])

        with torch.no_grad():
            inputs = self.get_inputs(pairs).to(self.model.device)
            all_scores = self.model(**inputs,
                                    return_dict=True,
                                    cutoff_layers=[28])
            scores = [
                scores[:, -1].view(-1, ).float() for scores in all_scores[0]
            ]
            scores = scores[0].cpu().numpy()
            # get descending order
            return scores.argsort()[::-1][0:self.topn]


class LLMCompressionRetriever:

    def __init__(self, base_compressor: LLMReranker,
                 base_retriever: Embedder):
        self.reranker = base_compressor
        self.retriever = base_retriever

    def get_relevant_documents(self, query: str):
        docs = self.retriever.get_relevant_documents(query)
        if not docs:
            return []
        chunks = []
        for doc in docs:
            chunks.append(doc.page_content)

        indexes = self.reranker.sort(chunks=chunks, query=query)
        return [docs[i] for i in indexes]
