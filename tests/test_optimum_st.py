from pathlib import Path

import torch
import torch.nn.functional as F
from optimum.onnxruntime import ORTModelForFeatureExtraction
# from optimum.onnxruntime.configuration import AutoQuantizationConfig
from transformers import AutoTokenizer, Pipeline


# copied from the model card
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[
        0]  #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(
        token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
        input_mask_expanded.sum(1), min=1e-9)


# optimum-cli export onnx -m  /workspace/models/text2vec-large-chinese/  --task  feature-extraction  --fp16 --device cuda --monolith   --trust-remote-code o4-opt-onnx/ --framework pt --optimize O2
class SentenceEmbeddingPipeline(Pipeline):

    def _sanitize_parameters(self, **kwargs):
        # we don't have any hyperameters to sanitize
        preprocess_kwargs = {}
        return preprocess_kwargs, {}, {}

    def preprocess(self, inputs):
        encoded_inputs = self.tokenizer(inputs,
                                        padding=True,
                                        truncation=True,
                                        return_tensors='pt')
        return encoded_inputs

    def _forward(self, model_inputs):
        outputs = self.model(**model_inputs)
        return {
            'outputs': outputs,
            'attention_mask': model_inputs['attention_mask']
        }

    def postprocess(self, model_outputs):
        # Perform pooling
        sentence_embeddings = mean_pooling(model_outputs['outputs'],
                                           model_outputs['attention_mask'])
        # Normalize embeddings
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings


def export_onnx():
    # https://github.com/philschmid/optimum-transformers-optimizations/blob/master/sentence-transformers.ipynb
    model_id = '/workspace/models/text2vec-large-chinese'
    onnx_path = Path('onnx')

    # load vanilla transformers and convert to onnx
    model = ORTModelForFeatureExtraction.from_pretrained(
        model_id, from_transformers=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # save onnx checkpoint and tokenizer
    model.save_pretrained(onnx_path)
    tokenizer.save_pretrained(onnx_path)
    # init pipeline


def profiling():
    onnx_path = 'o4-opt-onnx'
    model = ORTModelForFeatureExtraction.from_pretrained(
        onnx_path, file_name='model.onnx')
    model.to('cuda')

    tokenizer = AutoTokenizer.from_pretrained(onnx_path)
    vanilla_emb = SentenceEmbeddingPipeline(model=model, tokenizer=tokenizer)
    pred = vanilla_emb(
        'Could you assist me in finding my lost card? vanilla_emb')
    print(pred[0][:5])

    onnx_path = 'onnx'
    model = ORTModelForFeatureExtraction.from_pretrained(
        onnx_path, file_name='model.onnx')
    model.to('cuda')
    tokenizer = AutoTokenizer.from_pretrained(onnx_path)
    q8_emb = SentenceEmbeddingPipeline(model=model, tokenizer=tokenizer)
    pred = q8_emb('Could you assist me in finding my lost card? q8_emb')
    print(pred[0][:5])

    from time import perf_counter

    import numpy as np

    payload = 'Hello, my name is Philipp and I live in Nuremberg, Germany. Currently I am working as a Technical Lead at Hugging Face to democratize artificial intelligence through open source and open science. In the past I designed and implemented cloud-native machine learning architectures for fin-tech and insurance companies. I found my passion for cloud concepts and machine learning 5 years ago. Since then I never stopped learning. Currently, I am focusing myself in the area NLP and how to leverage models like BERT, Roberta, T5, ViT, and GPT2 to generate business value. I cannot wait to see what is next for me'
    print(f'Payload sequence length: {len(tokenizer(payload)["input_ids"])}')

    def measure_latency(pipe):
        latencies = []
        # warm up
        for _ in range(4):
            _ = pipe(payload)
        # Timed run
        for _ in range(20):
            start_time = perf_counter()
            _ = pipe(payload)
            latency = perf_counter() - start_time
            latencies.append(latency)
        # Compute run statistics
        time_avg_ms = 1000 * np.mean(latencies)
        time_std_ms = 1000 * np.std(latencies)
        time_p95_ms = 1000 * np.percentile(latencies, 95)
        return f'P95 latency (ms) - {time_p95_ms}; Average latency (ms) - {time_avg_ms:.2f} +\- {time_std_ms:.2f};', time_p95_ms

    vanilla_model = measure_latency(vanilla_emb)
    quantized_model = measure_latency(q8_emb)

    print(f'Vanilla model: {vanilla_model[0]}')
    print(f'Quantized model: {quantized_model[0]}')
    print(
        f'Improvement through quantization: {round(vanilla_model[1]/quantized_model[1],2)}x'
    )


profiling()
