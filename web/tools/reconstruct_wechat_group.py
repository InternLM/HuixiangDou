import argparse
import os
import time
import pdb
import pytoml
import requests
import json
from loguru import logger

def parse_args():
    """Parse args."""
    parser = argparse.ArgumentParser(description='Reconstruct group chat.')
    parser.add_argument('--output_dir',
                        type=str,
                        default='groups',
                        help='Splitted group messages.')
    parser.add_argument('--input',
                        type=str,
                        # default='/home/khj/github/huixiangdou/tests/history_recv_send.txt',
                        default='/home/khj/github/huixiangdou/web/tools/groups/18356748488@chatroom.jsonl',
                        help='Raw input messages.')
    parser.add_argument('--action',
                        type=str,
                        # default='split',
                        default='visualize',
                        help='action support:\n"split": split raw input into group messages; \n"visualize": visualize a group messges')
    
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

def visualize(_input):
    if not os.path.exists(_input):
        logger.error('{} not exist'.format(_input))
        return
    
    if not _input.endswith('.jsonl'):
        logger.error('{} show ends with .jsonl')
        return

    sender_cnt = {}

    with open(_input) as f:
        with open('chat.txt', 'w') as fout:
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
                formatted_str = '{}\t {}\t {}\t {}\n'.format(show_type, sender, text, recvs)
                fout.write(r"%s" % formatted_str)

    # for k, v in sender_cnt.items():
    #     if v > 2000:
    #         print((k, v))

def main():
    args = parse_args()
    if args.action == 'split':
        split(args.input, args.output_dir)
    elif args.action == 'visualize':
        visualize(args.input)

if __name__ == '__main__':
    main()
