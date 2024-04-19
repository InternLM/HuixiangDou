import argparse
import os
import time
import pdb
import pytoml
import requests
import json
from loguru import logger
import re

import argparse
import json

import pytoml
import requests
from loguru import logger


class ChatClient:
    """A class to handle client-side interactions with a chat service.

    This class is responsible for loading configurations from a given path,
    building prompts, and generating responses by interacting with the chat
    service.
    """

    def __init__(self, config_path: str) -> None:
        """Initialize the ChatClient with the path of the configuration
        file."""
        self.config_path = config_path
        self.llm_config = None
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.llm_config = config['llm']

    def build_prompt(self,
                     history_pair,
                     instruction: str,
                     template: str,
                     context: str = '',
                     reject: str = '<reject>'):
        """Build a prompt for interaction.

        Args:
            history_pair (list): List of previous interactions.
            instruction (str): Instruction for the current interaction.
            template (str): Template for constructing the interaction.
            context (str, optional): Context of the interaction. Defaults to ''.  # noqa E501
            reject (str, optional): Text that indicates a rejected interaction. Defaults to '<reject>'.  # noqa E501

        Returns:
            tuple: A tuple containing the constructed instruction and real history.
        """
        if context is not None and len(context) > 0:
            instruction = template.format(context, instruction)

        real_history = []
        for pair in history_pair:
            if pair[1] == reject:
                continue
            if pair[0] is None or pair[1] is None:
                continue
            if len(pair[0]) < 1 or len(pair[1]) < 1:
                continue
            real_history.append(pair)

        return instruction, real_history

    def auto_fix(self, backend):
        """Choose real backend according to config.ini."""

        enable_local, enable_remote = (self.llm_config['enable_local'],
                                       self.llm_config['enable_remote'])
        local_len, remote_len = (
            self.llm_config['server']['local_llm_max_text_length'],
            self.llm_config['server']['remote_llm_max_text_length'])

        max_length = local_len
        if enable_remote:
            max_length = remote_len

        if backend == 'local' and not enable_local:
            backend = self.llm_config['server']['remote_type']
            max_length = remote_len
        elif backend != 'local' and not enable_remote:
            backend = 'local'
            max_length = local_len

        return backend, max_length

    def generate_response(self, prompt, history=[], backend='local'):
        """Generate a response from the chat service.

        Args:
            prompt (str): The prompt to send to the chat service.
            history (list, optional): List of previous interactions. Defaults to [].
            backend (str, optional): Determine which LLM should be called. Default to `local`

        Returns:
            str: Generated response from the chat service.
        """
        url = self.llm_config['client_url']
        real_backend, max_length = self.auto_fix(backend=backend)

        if len(prompt) > max_length:
            logger.warning(
                f'prompt length {len(prompt)}  > max_length {max_length}, truncated'  # noqa E501
            )
            prompt = prompt[0:max_length]

        try:
            header = {'Content-Type': 'application/json'}
            data_history = []
            for item in history:
                data_history.append([item[0], item[1]])
            data = {
                'prompt': prompt,
                'history': data_history,
                'backend': real_backend
            }
            resp = requests.post(url,
                                 headers=header,
                                 data=json.dumps(data),
                                 timeout=300)
            if resp.status_code != 200:
                raise Exception(str((resp.status_code, resp.reason)))

            json_obj = resp.json()
            text = json_obj['text']
            if 'error' in json_obj:
                error = json_obj['error']
                if len(error) > 0:
                    logger.error(error)
            return text
        except Exception as e:
            logger.error(str(e))
            logger.error(
                'Do you forget `--standalone` when `python3 -m huixiangdou.main` ?'  # noqa E501
            )
            return ''

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Reconstruct group chat.')
    parser.add_argument('--output_dir',
                        type=str,
                        default='groups',
                        help='Splitted group messages.')
    parser.add_argument('--input',
                        type=str,
                        default='/home/khj/github/huixiangdou/tests/history_recv_send.txt',
                        help='Raw input messages.')
    parser.add_argument('--action',
                        type=str,
                        # default='split',
                        # default='visualize',
                        default='intention',
                        help='"split"): split raw input into group messages; "visualize"): visualize a group messges; "intention"): decide which query being a question')
    
    args = parser.parse_args()
    return args


def split(_input, output_dir):
    if not os.path.exists(_input):
        logger.error('{} not exist'.format(_input))
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    groups = {}
    json_str = ''
    with open(_input) as f:
        while True:
            line = f.readline()
            if not line:
                break
            json_str += line
            if line == '}\n':
                try:
                    json_obj = json.loads(json_str)
                    if 'data' in json_obj:
                        # normal message
                        data = json_obj['data']
                        data['messageType'] = json_obj['messageType']
                        
                        if 'fromGroup' in data:
                            group_id = data['fromGroup']
                            if group_id in groups:
                                groups[group_id].append(data)
                            else:
                                groups[group_id] = [data]
                            json_str = ''
                            continue
                        
                        logger.error((json_str, 'no fromGroup'))

                    if "answer" in json_obj:
                        # assistant message
                        if 'groupId' in json_obj:
                            group_id = json_obj['groupId']
                            if group_id in groups:
                                groups[group_id].append(data)
                            else:
                                groups[group_id] = [data]
                            json_str = ''
                            continue
                        
                        logger.error((json_str, 'has answer but no groupId'))

                except Exception as e:
                    # pdb.set_trace()
                    logger.error((e, json_str))
                json_str = ''

    msg_sum = 0
    for group_id, message_list in groups.items():
        msg_sum += len(message_list)
        logger.info('{} {}'.format(group_id, len(message_list)))
        filepath = os.path.join(output_dir, "{}.jsonl".format(group_id))
        with open(filepath, 'w') as f:
            for message in message_list:
                msg_json_str = json.dumps(message, ensure_ascii=False)
                f.write(msg_json_str)
                f.write('\n')
    logger.info('sum message {}'.format(msg_sum))

def remove_at_name(text):
    pattern = r'@[\w\.-]+\s+'
    text = re.sub(pattern, '', text)
    pos = text.find('@')
    if pos != -1:
        text = text[0:pos]
    return text

def visualize(output_dir):
    if not os.path.exists(output_dir):
        logger.error('{} not exist'.format(output_dir))
        return
    
    sender_cnt = {}

    files = os.listdir(output_dir)
    for file in files:
        filepath = os.path.join(output_dir, file)
        if not filepath.endswith('@chatroom.jsonl'):
            continue

        name = os.path.basename(filepath).split('.')[0]
        idx = 0
        with open(filepath) as f:
            with open(os.path.join(output_dir, '{}@reconstruct.txt'.format(name)), 'w') as fout:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    if len(line) < 2:
                        continue
                    json_obj = json.loads(line)

                    msg_type = json_obj['messageType']
                    show_type = ''

                    text = json_obj['content']
                    sender = json_obj['fromUser']
                    recvs = []

                    # get show_type and content text
                    if msg_type in [5, 9, '80001']:
                        show_type = 'normal'
                        if 'atlist' in json_obj:
                            show_type = 'normal_at'
                            atlist = json_obj['atlist']
                            for at in atlist:
                                if len(at) > 0:
                                    recvs.append(at)

                    if msg_type in [6, '80002']:
                        show_type = 'image'
                        text = '[图片]'

                    elif msg_type == '80009':
                        show_type = 'file'
                        content = json_obj['pushContent']

                    elif msg_type in [14, '80014']:
                        # ref revert msg
                        show_type = 'ref'
                        if 'title' in json_obj:
                            content = json_obj['title']
                        else:
                            content = 'unknown'
                        
                        if 'toUser' in json_obj:
                            recvs.append(json_obj['toUser'])

                    else:
                        show_type = 'other'
                        # print('other type {}'.format(msg_type))

                    if sender not in sender_cnt:
                        sender_cnt[sender] = 1
                    else:
                        sender_cnt[sender] += 1
                
                    if '<?xml version="1.0"?>' in text:
                        text = 'xml msg'
                    if '<sysmsg' in text:
                        text = 'sys msg'
                    if '<msg><emoji' in text:
                        text = 'emoji'
                    if '<msg>' in text and '<op id' in text:
                        text = 'app msg' 

                    text = remove_at_name(text)
                    
                    obj = {
                        'id': idx,
                        'show': show_type,
                        'sender': sender, 
                        'text': text,
                        'recvs': recvs
                    }
                    idx += 1
                    formatted_str = json.dumps(obj, ensure_ascii=False)
                    fout.write(formatted_str)
                    fout.write('\n')
                    # formatted_str = '{}\t {}\t {}\t {}\n'.format(show_type, sender, text, recvs)
                    # fout.write(r"%s" % formatted_str)

        # for k, v in sender_cnt.items():
        #     if v > 2000:
        #         print((k, v))


def is_question(query):
    llm = ChatClient('config.ini')
    SCORING_QUESTION_TEMPLTE = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'  # noqa E501
    prompt = SCORING_QUESTION_TEMPLTE.format(query)
    if prompt is None or len(prompt) == 0:
        return False

    score = 0
    relation = llm.generate_response(prompt=prompt, backend='puyu')
    filtered_relation = ''.join([c for c in relation if c.isdigit()])
    try:
        score_str = re.sub(r'[^\d]', ' ', filtered_relation).strip()
        score = int(score_str.split(' ')[0])
    except Exception as e:
        logger.error(str(e))
    if score >= 5:
        return True
    return False

def coref_res(target: object, window: list, group_intro: str):
    logger.debug('input window {}'.format(window))
    name_map = dict()
    name_int = ord('A')
    # chr(start_ascii + i)
    format_history = []
    for item in window:
        sender = item['sender']
        if sender not  in name_map:
            name_map[sender] = chr(name_int)
            name_int += 1

        format_history.append({
            'username': name_map[sender],
            'content': item['text']
        })

    target_sender = target['sender']
    if target_sender not  in name_map:
        name_map[target_sender] = chr(name_int)
        name_int += 1

    target_str = json.dumps({
        "username": name_map[target_sender],
        "content": target['text']
    }, indent=2, ensure_ascii=False)

    PROMPT_TEMPLATE = """请完成群聊场景中的指代消解任务。
群描述：{}
以下是历史对话，可能有多个人的发言：
{}

输入内容：
{}
content 指代消解后的结果是？如果不需要消解就返回空白。直接返回消解后的完整文本不要解释"""
    prompt = PROMPT_TEMPLATE.format(group_intro, json.dumps(format_history, ensure_ascii=False), target_str)

    logger.debug('output prompt {}'.format(prompt))
    llm = ChatClient('config.ini')
    response = llm.generate_response(prompt=prompt, backend='puyu')
    print(prompt, response)
    

def intention(output_dir):
    if not os.path.exists(output_dir):
        logger.error('{} not exist'.format(output_dir))
        return

    sender_cnt = {}

    group_intros = {
        '18356748488': """请完成群聊场景中的指代消解任务。

名词解释：        
HuixiangDou，中文名 茴香豆。
茴香豆是一个基于 LLM 的群聊知识助手，优势：

设计拒答、响应两阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。精髓见技术报告
成本低至 1.5G 显存，无需训练适用各行业
提供一整套前后端 web、android、算法源码，工业级开源可商用
查看茴香豆已运行在哪些场景；加入微信群直接体验群聊助手效果。

群描述：
这是 HuixiangDou (茴香豆) 的微信体验群。用户会发一些相关技术疑问。""",
    }

    files = os.listdir(output_dir)

    for file in files:
        filepath = os.path.join(output_dir, file)
        if not filepath.endswith('@chatroom@reconstruct.txt'):
            continue

        introduction = ''
        group_id = os.path.basename(filepath)
        group_id = group_id.split('@')[0]
        if group_id in group_intros:
            introduction = group_intros[group_id]
        
        if len(introduction) < 1:
            continue

        window_history = []
        MAX_WINDOW_SIZE = 8
        with open(filepath) as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if len(line) < 2:
                    continue
                json_obj = json.loads(line)
                if json_obj['show'] == 'ref':
                    continue
                
                text = json_obj['text']
                if len(text) < 1:
                    continue

                window_history.append(json_obj)
                if is_question(text):
                    json_obj['is_question'] = True
                    # 是问题，格式化历史消息，消解
                    window_history = window_history[-MAX_WINDOW_SIZE:-1]
                    cr_text = coref_res(json_obj, window=window_history, group_intro=introduction)
                    json_obj['cr_text'] = cr_text

                else:
                    json_obj['is_question'] = False

                # 判断是否问题
                # 如果是，尝试指代消解 & 意图划分

                outfilepath = filepath+'.1'
                with open(outfilepath, 'a') as fout:
                    json_text = json.dumps(json_obj, ensure_ascii=False)
                    fout.write(json_text)
                    fout.write('\n') 

def main():
    args = parse_args()
    if args.action == 'split':
        split(args.input, args.output_dir)
    elif args.action == 'visualize':
        visualize(args.output_dir)
    elif args.action == 'intention':
        intention(args.output_dir)

if __name__ == '__main__':
    main()
