# Copyright (c) OpenMMLab. All rights reserved.
import json

import torch
from transformers.generation import GenerationConfig

# Note: The default behavior now has injection attack prevention off.
DIR = '/internlm/ampere_7b_v1_7_0'
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(DIR, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(DIR,
                                             trust_remote_code=True,
                                             device_map='auto').eval()


def task1_intention():
    """Test prompt."""
    ret = []
    with open('data.json', encoding='utf8') as f:
        items = json.load(f)
    for idx, item in enumerate(items):
        question = item['question']

        prompt = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 1～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'.format(
            question)
        answer, _ = model.chat(tokenizer, prompt, history=[], top_k=1)
        print((answer, prompt))

        ret.append({'question': prompt, 'answer': answer})

        with open('task1_intention_internlm_prompt.json', 'w',
                  encoding='utf8') as f:
            json.dump(list(ret), f, ensure_ascii=False, indent=2)
        print('{}/{}'.format(idx, len(items)))


if __name__ == '__main__':
    task1_intention()
