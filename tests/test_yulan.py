import torch
from transformers import LlamaForCausalLM, LlamaTokenizer

model_path = '/models/YuLan-Chat-2-13b-fp16'
tokenizer = LlamaTokenizer.from_pretrained(model_path)
model = LlamaForCausalLM.from_pretrained(model_path,
                                         torch_dtype=torch.float16,
                                         device_map='auto')
model = model.eval()


def run(input_text: str):
    prompt = "The following is a conversation between a human and an AI assistant namely YuLan, developed by GSAI, Renmin University of China. The AI assistant gives helpful, detailed, and polite answers to the user's questions.\n[|Human|]:{}\n[|AI|]:".format(
        input_text)
    inputs = tokenizer(prompt,
                       return_tensors='pt',
                       padding='longest',
                       max_length=8192,
                       truncation=True,
                       return_attention_mask=True,
                       add_special_tokens=True)
    print(inputs)
    kwargs = {
        'temperature': 0.8,
        'top_p': 0.95,
        'top_k': 50,
        'repetition_penalty': 1.1,
        'no_repeat_ngram_size': 64,
        'max_length': 8192,
        'pad_token_id': tokenizer.bos_token_id,
        'eos_token_id': tokenizer.eos_token_id
    }
    outputs = model.generate(inputs['input_ids'].to(model.device),
                             attention_mask=inputs['attention_mask'].to(
                                 model.device),
                             do_sample=True,
                             **kwargs)
    print(tokenizer.batch_decode(outputs, skip_special_tokens=True))


texts = [
    'mmdeploy extract如何使用', 'OpenMMLab与上海AI lab 的关系是什么？', 'MMEngine 和MMCV的区别',
    'openmmlab 是什么？', 'mmdet3.0 是否依赖 mmcv0.7', 'mmdet3.0对应的mmcv最低版本是多少'
]
for input_text in texts:
    run(input_text)
