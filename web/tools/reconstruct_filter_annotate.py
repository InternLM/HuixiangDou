# 1. puyu 在判断是否是问题任务中，召回已经很高
# 2. 用 kimi 二次确认是否是个问题
# 3. 在已经  is_question true 中，手工标注是否需要 cr
# * 标注规范：就看这句话是不是能构成独立的问题、不需要看其他话
# * kimi & puyu 同时认为需要解答的内容中， puyu cr 判定的正确率

"""
在群聊场景中进行意图消解，即理解并处理群聊中用户表达的意图，是一个复杂的过程，因为它涉及到多个人、多种语境和可能的歧义。
以下是一些在群聊场景中进行意图消解时应该注意的要点：

上下文理解：理解每个发言的上下文是至关重要的。群聊中的对话往往是非线性的，可能会有多条线索同时进行。
用户识别：识别发言者的身份可以帮助理解其发言背后的意图，尤其是在有多个参与者的情况下。
话题跟踪：群聊中的话题可能会快速变化，跟踪当前的讨论主题对于正确理解意图至关重要。
歧义处理：群聊中的信息往往更加随意和含糊，需要能够处理语言上的歧义。
情感分析：理解发言者的情感状态可以帮助更准确地把握其意图。
礼貌和文化差异：群聊中可能包含来自不同文化背景的人，理解和尊重这些差异对于正确消解意图很重要。
指令识别：在群聊中，用户可能会发出指令或请求，识别这些指令并作出适当的响应是必要的。
信息过滤：群聊中可能包含大量的信息，能够过滤掉无关信息，专注于相关的对话片段。
隐私和安全：在处理群聊数据时，保护用户隐私和数据安全是非常重要的。
响应时间：在群聊中，及时响应可以提升用户体验，但也要注意不要过早地打断正在进行的对话。
多任务处理：群聊可能同时涉及多个话题或任务，能够同时处理多个意图是有帮助的。
错误处理：当理解出现偏差时，能够优雅地处理错误并从用户那里获得反馈以改进是重要的。
用户引导：在必要时，引导用户提供更清晰的信息或指令，以帮助更好地理解其意图。
适应性：群聊的动态性要求系统能够适应不断变化的对话模式和用户行为。
记录和回顾：有时候，为了理解当前的发言，可能需要回顾之前的聊天记录。
"""
import json
import pdb
import os
import re
from loguru import logger
from openai import OpenAI
import tty
import sys
import termios
import select
import time
API_KEY = os.getenv('MOONSHOT_API_KEY')
if API_KEY is None or len(API_KEY) < 1:
    assert('moonshot api key not set')

client = OpenAI(
    api_key=API_KEY,
    base_url='https://api.moonshot.cn/v1',
)

def build_context(sender: str, query: str, window: list):
    context = ""
    for item in window:
        context += "{}: {}\n".format(item['sender'], item['text'])

    context += "标注问题：\n"
    context += "{}: {}\n".format(sender, query)
    return context

# 定义输入输出文件路径
GROUP_ID = "20814553575"
# 18356748488  ncnn contributor's group
# 20814553575  openmmlab groups
puyu_file_path = 'groups/{}@chatroom@reconstruct.txt.llm'.format(GROUP_ID)
kimi_file_path = 'groups/{}@chatroom@reconstruct.txt.kimi'.format(GROUP_ID)
gt_file_path = 'groups/{}@chatroom@gt.jsonl'.format(GROUP_ID)

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


def kimi_annotate():
    # 读取输入文件，并逐行处理
    with open(puyu_file_path, 'r', encoding='utf-8') as input_file, open(kimi_file_path, 'w', encoding='utf-8') as output_file:
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
        

def human_annotate():
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
                kimi_is_not_question +=1
                continue
            if len(data['text']) < 7:
                too_short += 1
                continue
            datas.append(data)
    logger.debug("sum: {}, kimi_is_question: {}, kimi_is_not_question {}, miss_key {} too_short {}".format(line_idx, len(datas), kimi_is_not_question, miss_key, too_short))

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

            context = build_context(sender=sender, query=text, window=cr_window)
            print("{} / {}".format(idx, max_len))
            print(context)
            
            # 等待用户输入
            while True:
                user_input = sys.stdin.read(1)
                if user_input not in ['j', 'k', 'i']:
                    print("Invalid input. Please enter 'j' or 'k' (yes, no or none). ")
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
    print("Annotation completed. Check the output file for the results.")


def human_check():
    bad = []
    good = []
    with open(gt_file_path) as f:
        for idx, line in enumerate(f):
            data = json.loads(line)

            # print(repr('{} | {} | {}'.format(idx, data['cr_need_gt'], data['text'])))
            # time.sleep(0.5)
            
            if data['cr_need_gt']:
                bad.append(repr(data['text']))
            else:
                good.append(repr(data['text']))
    

    
    print(json.dumps(bad, indent=2, ensure_ascii=False))
    print(json.dumps(good, indent=2, ensure_ascii=False))
    print("bad count {}, good count {}".format(len(bad), len(good)))
# kimi_annotate()
human_annotate()
human_check()
