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


def build_context(sender: str, query: str, window: list):
    context = ''
    for item in window:
        context += '{}: {}\n'.format(item['sender'], item['text'])

    context += '标注问题：\n'
    context += '{}: {}\n'.format(sender, query)
    return context


def kimi_is_question(query):
    SCORING_QUESTION_TEMPLTE = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句或在向其他人问问题，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'  # noqa E501
    prompt = SCORING_QUESTION_TEMPLTE.format(query)
    if prompt is None or len(prompt) == 0:
        return False

    messages = [{
        'role':
        'system',
        'content':
        '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'
    }, {
        'role': 'user',
        'content': prompt
    }]

    API_KEY = os.getenv('MOONSHOT_API_KEY')
    if API_KEY is None or len(API_KEY) < 1:
        assert ('moonshot api key not set')

    client = OpenAI(
        api_key=API_KEY,
        base_url='https://api.moonshot.cn/v1',
    )

    try:
        completion = client.chat.completions.create(
            model='moonshot-v1-8k',
            messages=messages,
            temperature=0.0,
        )
        relation = completion.choices[0].message.content
        filtered_relation = ''.join([c for c in relation if c.isdigit()])
        try:
            score_str = re.sub(r'[^\d]', ' ', filtered_relation).strip()
            score = int(score_str.split(' ')[0])
            if score >= 5:
                return True
        except Exception as e:
            logger.error(str(e))
    except Exception as e:
        return str(e)
    return False


def kimi_annotate(puyu_file_path: str, kimi_file_path: str):
    # 读取输入文件，并逐行处理
    with open(puyu_file_path, 'r', encoding='utf-8') as input_file, open(
            kimi_file_path, 'w', encoding='utf-8') as output_file:
        datas = []
        for line in input_file:
            # 解析JSON数据
            data = json.loads(line)

            if not data['is_question']:
                continue

            text = data['text']
            kimi_gt = kimi_is_question(query=text)
            logger.debug('{} --- {}'.format(text, kimi_gt))
            data['kimi_is_question'] = kimi_gt
            datas.append(data)

            output_file.write(json.dumps(data, ensure_ascii=False) + '\n')


def human_annotate(kimi_file_path: str, gt_file_path):
    # 读取输入文件，并逐行处理
    datas = []
    miss_key = 0
    kimi_is_not_question = 0
    line_idx = 0
    too_short = 0
    with open(kimi_file_path) as input_file:
        while True:
            line = input_file.readline()
            # 解析JSON数据
            line_idx += 1
            if not line:
                break
            data = json.loads(line)
            if 'kimi_is_question' not in data:
                miss_key += 1
                continue
            if data['kimi_is_question'] == False:
                kimi_is_not_question += 1
                continue
            if len(data['text']) < 7:
                too_short += 1
                continue
            datas.append(data)
    logger.debug(
        'sum: {}, kimi_is_question: {}, kimi_is_not_question {}, miss_key {} too_short {}'
        .format(line_idx, len(datas), kimi_is_not_question, miss_key,
                too_short))

    START_INDEX = 0

    # 保存原始的tty设置
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(sys.stdin)

    with open(gt_file_path, 'a', encoding='utf-8') as output_file:
        max_len = len(datas)
        datas = datas[START_INDEX:]

        for idx, data in enumerate(datas):
            # 显示上下文和文本
            cr_window = data.get('cr_window', {})
            text = data.get('text', '')
            sender = data.get('sender', '')

            context = build_context(sender=sender,
                                    query=text,
                                    window=cr_window)
            print('{} / {}'.format(idx, max_len))
            print(context)

            # 等待用户输入
            while True:
                user_input = sys.stdin.read(1)
                if user_input not in ['j', 'k', 'i']:
                    print(
                        "Invalid input. Please enter 'j' or 'k' (yes, no or none). "
                    )
                    continue
                # 检查用户输入是否有效
                print(user_input)
                break

            # 更新数据中的Ground Truth
            if user_input == 'j':
                data['cr_need_gt'] = True
            elif user_input == 'k':
                data['cr_need_gt'] = False
            elif user_input == 'i':
                data['cr_need_gt'] = 'not a question'

            # 将更新后的数据写入输出文件
            output_file.write(json.dumps(data, ensure_ascii=False) + '\n')

    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    print('Annotation completed. Check the output file for the results.')


def human_check(gt_file_path):
    bad = []
    bad_text_sum = 0
    good = []
    good_text_sum = 0
    with open(gt_file_path) as f:
        for idx, line in enumerate(f):
            data = json.loads(line)

            # print(repr('{} | {} | {}'.format(idx, data['cr_need_gt'], data['text'])))
            # time.sleep(0.5)

            if data['cr_need_gt']:
                bad.append(repr(data['text']))
                bad_text_sum += len(data['text'])
            else:
                good.append(repr(data['text']))
                good_text_sum += len(data['text'])

    print(json.dumps(bad, indent=2, ensure_ascii=False))
    print(json.dumps(good, indent=2, ensure_ascii=False))
    print(
        'bad count {}, avg text len {}; good count {}, avg text len {}'.format(
            len(bad), bad_text_sum / len(bad), len(good),
            good_text_sum / len(good)))

    with open('groups/good.json', 'w') as f:
        f.write(json.dumps(good, ensure_ascii=False, indent=2))

    with open('groups/bad.json', 'w') as f:
        f.write(json.dumps(bad, ensure_ascii=False, indent=2))


def metric(llm_type: str,
           gt_filepath: str = 'groups/input.jsonl',
           dt_filepath: str = 'groups/output.jsonl'):
    gts = []
    dts = []
    unknow_count = 0

    with open(gt_filepath) as gt:
        for line in gt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue

            cr_need_gt = json_obj['cr_need_gt']
            gts.append(cr_need_gt)

    with open(dt_filepath) as dt:
        for line in dt:
            json_obj = json.loads(line)
            if 'cr_need_gt' not in json_obj:
                continue

            dt = json_obj['{}_cr_need'.format(llm_type)]
            if 'yes' == dt:
                dts.append(True)
            elif 'no' == dt:
                dts.append(False)
            else:
                dt = dt.replace(' ', '')
                dt = dt.replace('\n', '')

                if 'ab' in dt or 'abc' in dt:
                    unknow_count += 1

                    dts.append(bool(1 - cr_need_gt))
                elif '答案：b' in dt or '选：b' in dt or '答案是：b' in dt:
                    dts.append(True)
                elif '答案是：a' in dt or '答案是"不需要"' in dt or '答案是：不需要' in dt or '答案：不需要' in dt or '选项结果：不需要' in dt or '结果选项：不需要':
                    dts.append(False)
                else:
                    unknow_count += 1
                    print(dt)
                    pdb.set_trace()
                    dts.append(bool(1 - cr_need_gt))

    assert len(gts) == len(dts)
    precision = precision_score(gts, dts)
    recall = recall_score(gts, dts)
    f1 = f1_score(gts, dts)

    logger.info('{}: {} {} {} {}'.format(llm_type, precision, recall, f1,
                                         unknow_count))


def qwen_coref_res(llm_type: str, target: object):
    model = '/workspace/models/{}'.format(llm_type)
    client = OpenAI(
        base_url='http://10.140.24.142:29999/v1',
        api_key='token-abc123',
    )

    group_intro = """
名词解释：
open-compass/opencompass : 用于评测大型语言模型（LLM）. 它提供了完整的开源可复现的评测框架，支持大语言模型、多模态模型的一站式评测，基于分布式技术，对大参数量模型亦能实现高效评测。评测方向汇总为知识、语言、理解、推理、考试五大能力维度，整合集纳了超过70个评测数据集，合计提供了超过40万个模型评测问题，并提供长文本、安全、代码3类大模型特色技术能力评测。
openmmlab/mmpose is an open-source toolbox for pose estimation based on PyTorch
openmmlab/mmdeploy is an open-source deep learning model deployment toolset
openmmlab/mmdetection is an open source object detection toolbox based on PyTorch.
lmdeploy 是一个用于压缩、部署和服务 LLM（Large Language Model）的工具包。是一个服务端场景下，transformer 结构 LLM 部署工具，支持 GPU 服务端部署，速度有保障，支持 Tensor Parallel，多并发优化，功能全面，包括模型转换、缓存历史会话的 cache feature 等. 它还提供了 WebUI、命令行和 gRPC 客户端接入。
茴香豆（HuixiangDou）是一个基于 LLM 的群聊知识助手。设计拒答、响应两阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。
xtuner is an efficient, flexible and full-featured toolkit for fine-tuning large models.
mmyolo : YOLO series toolbox and benchmark. Implemented RTMDet, RTMDet-Rotated,YOLOv5, YOLOv6, YOLOv7, YOLOv8,YOLOX, PPYOLOE, etc.
ncnn is a high-performance neural network inference framework optimized for the mobile platform
"""

    window = target['cr_window']
    # logger.debug('input window {}'.format(window))
    name_map = dict()
    name_int = ord('A')
    # chr(start_ascii + i)
    format_history = []
    for item in window:
        sender = item['sender']
        if sender not in name_map:
            name_map[sender] = chr(name_int)
            name_int += 1

        format_history.append({
            'username': name_map[sender],
            'content': item['text']
        })

    target_sender = target['sender']
    if target_sender not in name_map:
        name_map[target_sender] = chr(name_int)
        name_int += 1

    target_str = json.dumps(
        {
            'username': name_map[target_sender],
            'content': target['text']
        },
        indent=2,
        ensure_ascii=False)

    BASE_PROMPT_TEMPLATE = '''群聊场景中“这”、“它”、“哪”等代词需要查看上下文和其他用户的回复才能确定具体指什么，请完成群聊场景代词替换任务。

以下是历史对话，可能有多个人的发言：
{}

输入内容：
"{}"'''
    prompt_base = BASE_PROMPT_TEMPLATE.format(
        json.dumps(format_history, ensure_ascii=False), target_str)

    prompt = '{}\n输入内容中的 content 信息是否完整，是否需要从历史对话中提取代词或宾语来替代 content 中的一部分词汇？ A：不需要提取，信息完整  B：需要  C：不知道 \n一步步分析，首先历史消息包含哪些话题；其次哪个话题与问题最相关；如果都不相关就不提取。 '.format(
        prompt_base)

    completion = client.chat.completions.create(model=model,
                                                messages=[{
                                                    'role': 'user',
                                                    'content': prompt
                                                }])
    need_cr = completion.choices[0].message.content.lower()
    need_cr = need_cr.strip()
    logger.debug('{} {}'.format(prompt, need_cr))

    response = ''

    prompt = """请判断用户意图，这位用户在做单选题，单选题答案有 3 个， A：不需要提取，信息完整  B：需要  C：不知道。
用户输入：
{}

用户的答案是？不要解释，直接给 ABC 选项结果。
""".format(need_cr)

    completion = client.chat.completions.create(model=model,
                                                messages=[{
                                                    'role': 'user',
                                                    'content': prompt
                                                }])
    need_cr = completion.choices[0].message.content.lower()
    need_cr = need_cr.strip()

    logger.warning('final choose {}'.format(need_cr))

    if need_cr.startswith(
            'a'
    ) or need_cr == '不需要' or '因此不需要' in need_cr or 'a：不需要' in need_cr or '不需要进行指代消解' in need_cr or '选项 a' in need_cr:
        return '', 'no'
    elif need_cr.startswith(
            'b'
    ) or need_cr == '需要' or '因此需要' in need_cr or '因此选择b' in need_cr or '需要进行指代消解' in need_cr or '需要指代消解' in need_cr or 'b：需要' in need_cr:
        prompt = '{}\n指代消解输入内容中 content 后的文本是？直接返回消解后的完整文本不要解释原因；直接返回最终结果不要解释过程。'.format(
            prompt_base)

        completion = client.chat.completions.create(model=model,
                                                    messages=[{
                                                        'role': 'user',
                                                        'content': prompt
                                                    }])
        response = completion.choices[0].message.content.lower()
    elif need_cr.startswith('c') or '不知道' in need_cr:
        return '', 'unknown'
    else:
        return '', 'exception {}'.format(need_cr)

    keywords = ['指代消解后的文本是：', '指代消解后是：', '指代消解后：', '指代消解后的文本为：']
    for keyword in keywords:
        if keyword in response:
            response = response.split(keyword)[-1]
    response = response.strip()
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    logger.warning('coref response {}'.format(response))
    return response, 'yes'


def llm_annotate(llm_type: str,
                 input_filepath: str = 'groups/input.jsonl',
                 output_filepath: str = 'groups/output.jsonl'):
    idx = 0
    with open(input_filepath) as fin, open(output_filepath, 'a') as fout:
        for line in fin:
            json_obj = json.loads(line)
            if not json_obj['is_question']:
                continue
            if not json_obj['kimi_is_question']:
                continue

            idx += 1

            if 'qwen' in llm_type.lower():
                cr_text, state = qwen_coref_res(llm_type=llm_type,
                                                target=json_obj)
            json_obj['{}_cr_text'.format(llm_type)] = cr_text
            json_obj['{}_cr_need'.format(llm_type)] = state

            json_text = json.dumps(json_obj, ensure_ascii=False)
            fout.write(json_text)
            fout.write('\n')


def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(
        description='Annotate and metric LLM with CR task.')
    parser.add_argument('--group-id',
                        type=str,
                        default='20814553575',
                        help='Group ID')
    parser.add_argument(
        '--input',
        type=str,
        default='/home/khj/github/huixiangdou/tests/history_recv_send.txt',
        help='Raw input messages.')
    parser.add_argument(
        '--action',
        type=str,
        # default='split',
        default='metric',
        help=
        '"annotate"): manually annotate query; "metric"): test with LLM and metric'
    )
    parser.add_argument(
        '--llm-type',
        type=str,
        # default='split',
        # default='Qwen1.5-0.5B-Chat',
        default='Qwen1.5-1.8B-Chat',
        # default='qwen1.5-moe-2.7B-chat',
        # default='Qwen1.5-4B-Chat',
        # default='Qwen1.5-7B-Chat',
        # default='Qwen1.5-14B-Chat',
        # default='Qwen1.5-32B-Chat',
        help='LLM type, use qwen moe by default.')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    # 定义输入输出文件路径
    # 18356748488  ncnn contributor's group
    # 20814553575  openmmlab groups

    if args.action == 'annotate':
        """
        1. 用 kimi 二次标注，基于 `reconstruct_wechat_group.py is_question` 筛选
        2. kimi & LLM 同时认为是问题的，过滤太短的，人工标注
        3. 检查一遍
        4. 基于人工 GT 计算 LLM 的精度
        """
        group_id = args.group_id
        puyu_file_path = 'groups/{}@chatroom@reconstruct.txt.llm'.format(
            group_id)
        kimi_file_path = 'groups/{}@chatroom@reconstruct.txt.kimi'.format(
            group_id)
        gt_filepath = 'groups/{}@chatroom@gt.jsonl'.format(group_id)
        kimi_annotate()
        human_annotate()
    elif args.action == 'check':
        human_check('groups/input.jsonl')
    elif args.action == 'metric':
        output_filepath = 'groups/{}.jsonl'.format(args.llm_type)
        llm_annotate(llm_type=args.llm_type, output_filepath=output_filepath)
        metric(llm_type=args.llm_type, filepath=output_filepath)

        # for llm_type in ['Qwen1.5-0.5B-Chat','Qwen1.5-1.8B-Chat', 'qwen1.5-moe-2.7B-chat', 'Qwen1.5-4B-Chat', 'Qwen1.5-7B-Chat', 'Qwen1.5-14B-Chat', 'Qwen1.5-32B-Chat']:
        #     input_filepath = 'groups/{}.jsonl'.format(llm_type)
        #     metric(llm_type=llm_type, gt_filepath='groups/input.jsonl', dt_filepath=input_filepath)
