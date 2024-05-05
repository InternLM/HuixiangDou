import argparse
import json
import os
import pdb
import re
import time

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
    parser.add_argument(
        '--input',
        type=str,
        default='/home/khj/github/huixiangdou/tests/history_recv_send.txt',
        help='Raw input messages.')
    parser.add_argument(
        '--action',
        type=str,
        # default='split',
        default='intention',
        help=
        '"split"): split raw input into group messages; "intention"): decide which query being a question'
    )

    args = parser.parse_args()
    return args


def remove_at_name(text):
    pattern = r'@[\w\.-]+\s+'
    text = re.sub(pattern, '', text)
    pos = text.find('@')
    if pos != -1:
        text = text[0:pos]
    return text


def simplify_wx_object(json_obj):
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
        'show': show_type,
        'sender': sender,
        'text': text,
        'recvs': recvs,
        'timestamp': json_obj['timestamp']
    }
    return obj


def split(_input, output_dir):
    """把一个完整的聊天日志，简化、划成不同群的群聊记录。"""
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

                    if 'answer' in json_obj:
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

        if len(message_list) < 1000:
            logger.debug('msg count number too small, skip dump')
            continue

        filepath = os.path.join(output_dir,
                                '{}@reconstruct.txt'.format(group_id))
        with open(filepath, 'w') as fout:
            idx = 0
            for json_obj in message_list:

                obj = simplify_wx_object(json_obj)
                obj['id'] = idx
                idx += 1

                fout.write(json.dumps(obj, ensure_ascii=False))
                fout.write('\n')

    logger.info('sum message {}'.format(msg_sum))


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
    llm = ChatClient('config.ini')

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

    BASE_PROMPT_TEMPLATE = '''请完成群聊场景中的指代消解任务。
"{}"
以下是历史对话，可能有多个人的发言：
{}

输入内容：
"{}"'''
    prompt_base = BASE_PROMPT_TEMPLATE.format(
        group_intro, json.dumps(format_history, ensure_ascii=False),
        target['text'])

    prompt = '{}\n输入是否需要指代消解？ A：需要  B不需要 C不知道'.format(prompt_base)
    need_cr = llm.generate_response(prompt=prompt, backend='puyu').lower()
    logger.debug('{} {}'.format(prompt, need_cr))

    response = ''
    if 'a' in need_cr:
        prompt = '{}\n指代消解输入后的结果是？直接返回消解后的完整文本不要解释原因；直接返回最终结果不要解释过程。'.format(
            prompt_base)
        response = llm.generate_response(prompt=prompt, backend='puyu').lower()
    else:
        return '', False

    keywords = ['指代消解后的文本是：', '指代消解后是：', '指代消解后：', '指代消解后的文本为：']
    for keyword in keywords:
        if keyword in response:
            response = response.split(keyword)[-1]
    response = response.strip()
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    logger.debug('return response {}'.format(response))
    return response, True


def intention(output_dir):
    """扫描一个群的流式聊天记录，把同一个人 18 秒内发的连续内容合并."""
    if not os.path.exists(output_dir):
        logger.error('{} not exist'.format(output_dir))
        return

    sender_cnt = {}

    #     group_intros = {
    #         '18356748488': """
    # 名词解释：
    # HuixiangDou，中文名 茴香豆。
    # 茴香豆是一个基于 LLM 的群聊知识助手，优势：

    # 设计拒答、响应两阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。精髓见技术报告
    # 成本低至 1.5G 显存，无需训练适用各行业
    # 提供一整套前后端 web、android、算法源码，工业级开源可商用
    # 查看茴香豆已运行在哪些场景；加入微信群直接体验群聊助手效果。

    # 群描述：
    # 这是 HuixiangDou (茴香豆) 的微信体验群。用户会发一些相关技术疑问。""",
    #     }
    group_intros = {
        '20814553575':
        """
名词解释：
open-compass/opencompass : 用于评测大型语言模型（LLM）. 它提供了完整的开源可复现的评测框架，支持大语言模型、多模态模型的一站式评测，基于分布式技术，对大参数量模型亦能实现高效评测。评测方向汇总为知识、语言、理解、推理、考试五大能力维度，整合集纳了超过70个评测数据集，合计提供了超过40万个模型评测问题，并提供长文本、安全、代码3类大模型特色技术能力评测。
openmmlab/mmpose is an open-source toolbox for pose estimation based on PyTorch
openmmlab/mmdeploy is an open-source deep learning model deployment toolset
openmmlab/mmdetection is an open source object detection toolbox based on PyTorch.
lmdeploy 是一个用于压缩、部署和服务 LLM（Large Language Model）的工具包。是一个服务端场景下，transformer 结构 LLM 部署工具，支持 GPU 服务端部署，速度有保障，支持 Tensor Parallel，多并发优化，功能全面，包括模型转换、缓存历史会话的 cache feature 等. 它还提供了 WebUI、命令行和 gRPC 客户端接入。
茴香豆（HuixiangDou）是一个基于 LLM 的群聊知识助手。设计拒答、响应两阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。
xtuner is an efficient, flexible and full-featured toolkit for fine-tuning large models.
mmyolo : YOLO series toolbox and benchmark. Implemented RTMDet, RTMDet-Rotated,YOLOv5, YOLOv6, YOLOv7, YOLOv8,YOLOX, PPYOLOE, etc.

群描述：
这是 openmmlab 贡献者和用户群。用户会发一些相关技术疑问。""",
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
        MAX_WINDOW_SIZE = 12
        STME_SPAN = 18

        raw_chats = []
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
                raw_chats.append(json_obj)

        # concat successive chat to one and save them
        idx = 0
        concat_chats = []
        target = None
        target_timestamp = 0
        while idx < len(raw_chats):
            chat = raw_chats[idx]
            idx += 1

            if chat['timestamp'] == target_timestamp:
                continue

            if target is None:
                target = chat
                target_timestamp = target['timestamp']
            elif target['sender'] == chat['sender'] and abs(
                    chat['timestamp'] - target_timestamp) < STME_SPAN:
                target_timestamp = chat['timestamp']
                # print('{} merge {}'.format(target['id'], chat['id']))
                target['text'] += '\n'
                target['text'] += chat['text']

            else:
                concat_chats.append(target)
                target = None

        if target is not None:
            concat_chats.append(target)

        outfilepath = filepath + '.concat'
        with open(outfilepath, 'w') as f:
            f.write(json.dumps(concat_chats, indent=2, ensure_ascii=False))

        logger.info('concat {} to {} msg'.format(len(raw_chats),
                                                 len(concat_chats)))

        # check a query is question, and coref res
        for json_obj in concat_chats:
            text = json_obj['text']
            if len(text) < 1:
                continue

            window_history.append(json_obj)
            if is_question(text):
                json_obj['is_question'] = True
                # 是问题，格式化历史消息，消解
                window_history = window_history[-MAX_WINDOW_SIZE:-1]
                cr_text, success = coref_res(json_obj,
                                             window=window_history,
                                             group_intro=introduction)

                json_obj['cr_window'] = window_history
                if success:
                    json_obj['cr_text'] = cr_text
                    json_obj['cr_need'] = True
                else:
                    json_obj['cr_need'] = False
            else:
                json_obj['is_question'] = False

            # 判断是否问题
            # 如果是，尝试指代消解 & 意图划分

            outfilepath = filepath + '.llm'
            with open(outfilepath, 'a') as fout:
                json_text = json.dumps(json_obj, ensure_ascii=False)
                fout.write(json_text)
                fout.write('\n')


def main():
    """
    split: 把单个群聊文件，划分成多个。
    intention: 用 LLM 计算 is_question cr_need
    """
    args = parse_args()
    if args.action == 'split':
        split(args.input, args.output_dir)
    elif args.action == 'intention':
        intention(args.output_dir)


if __name__ == '__main__':
    main()
