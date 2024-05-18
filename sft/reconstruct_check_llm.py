# 1. puyu 在判断是否是问题任务中，召回已经很高
# 2. 用 kimi 二次确认是否是个问题
# 3. 在已经  is_question true 中，手工标注是否需要 cr
# * 标注规范：就看这句话是不是能构成独立的问题、不需要看其他话
# * kimi & puyu 同时认为需要解答的内容中， puyu cr 判定的正确率

import argparse
import json
import os
import pdb
import re
import select
import sys
import termios
import time
import tty

from loguru import logger
from openai import OpenAI
from sklearn.metrics import f1_score, precision_score, recall_score


def read_badcase(llm_type: str, input_filepath: str):
    gts = []
    dts = []
    unknow_count = 0

    with open('groups/input.jsonl') as gt:
        for line in gt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue

            cr_need_gt = json_obj['cr_need_gt']
            gts.append(cr_need_gt)

    ret = dict()
    idx = 0
    with open(input_filepath) as dt:
        for line in dt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue

            dt = json_obj['{}_cr_need'.format(llm_type)] == 'yes'
            if dt != gts[idx]:
                ret[json_obj['text']] = line
            idx += 1
    return ret


if __name__ == '__main__':
    b14 = 'Qwen1.5-14B-Chat'
    b14_badcase = read_badcase(b14, 'groups/{}.jsonl'.format(b14))

    b32 = 'Qwen1.5-32B-Chat'
    b32_badcase = read_badcase(b32, 'groups/{}.jsonl'.format(b32))

    with open('groups/join.jsonl', 'w') as f:
        for k in b14_badcase.keys():
            if k in b32_badcase:
                json_str = b32_badcase[k]
                json_obj = json.loads(json_str)
                text = json_obj['text']
                gt = 'yes' if json_obj['cr_need_gt'] else 'no'
                dt = json_obj['{}_cr_need'.format(b32)]

                if dt == 'yes':
                    f.write('dt:{} \ttext:{}\n'.format(dt, text))
