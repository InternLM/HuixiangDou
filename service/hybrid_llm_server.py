import argparse
import os

from transformers import AutoModelForCausalLM, AutoTokenizer
from loguru import logger
import time
import json
import torch
import random
from aiohttp import web

class HybridLLMServer(object):

    def __init__(self, model_path: str = "/models/Qwen-14B-Chat", device: str = "cuda:2", max_length:int=40000) -> None:
        self.device = device
        self.max_length = max_length

        if model_path is None or not os.path.exists(model_path):
            raise Exception('{} not exist'.format(model_path))
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

        self.model = AutoModelForCausalLM.from_pretrained(
            "/models/Qwen-14B-Chat",
            trust_remote_code=True,
            device_map="auto",
            fp16=True,
        ).eval()

    def generate_response(self, prompt, history=[], retry=3, remote=False):
        output_text = ''
        time_tokenizer = time.time()

        if remote:
            # call kimi-chat
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("MOONSHOT_API_KEY"),
                base_url="https://api.moonshot.cn/v1",
            )

            messages=[{"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力，政治宗教等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"}]
            for item in history:
                messages.append({"role": "user", "content": item[0]})
                messages.append({"role": "system", "content": item[1]})
            messages.append({"role": "user", "content": prompt})

            life = 0
            while life < retry:
                try:
                    logger.debug('remote api sending: {}'.format(messages))
                    completion = client.chat.completions.create(
                        model="moonshot-v1-128k",
                        messages=messages,
                        temperature=0.3,
                    )
                    output_text = completion.choices[0].message.content  
                except Exception as e:
                    logger.error(str(e))
                    log_message = str(e).lower()
                    if 'cannot connect to proxy' in log_message:
                        # retry
                        life += 1
                        randval = random.randint(1, int(pow(2, life)))
                        time.sleep(randval)
                break
        else:
            output_text, _ = self.model.chat(self.tokenizer, prompt, history, top_k=1)
        time_finish = time.time()

        logger.debug('Q:{} A:{} \t\t remote {} timecost {} '.format(prompt[-100:-1], output_text, remote, time_finish - time_tokenizer))
        return output_text

    def build_prompt(self, history_pair, instruction: str, context: str = '', reject: str = '知识库没结果'):
        if context is not None and len(context) > 0:
            instruction = '阅读这些参考材料回答问题，材料可能和问题无关。如果无法确定答案，直接回答不知道。如果材料和问题无关，尝试用你自己的理解来回答问题。\n\n 材料：“{}\nopenmmlab 属于上海人工智能实验室。”\n\n 问题：“{}”'.format(context, instruction)
        # instruction = '{}。请仔细阅读材料，材料可能和问题无关。如果无法确定答案，直接回答不知道：{}'.format(context, instruction)

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

    # 将对话历史、插件信息聚合成一段初始文本
    def build_input_text(self, chat_history, list_of_plugin_info) -> str:
        # 将一个插件的关键信息拼接成一段文本的模版。
        TOOL_DESC = """{name_for_model}: Call this tool to interact with the {name_for_human} API. What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters}"""

        # ReAct prompting 的 instruction 模版，将包含插件的详细信息。
        PROMPT_REACT = """Answer the following questions as best you can. You have access to the following tools:

        {tools_text}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tools_name_text}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Begin!

        Question: {query}"""

        # 候选插件的详细信息
        tools_text = []
        for plugin_info in list_of_plugin_info:
            tool = TOOL_DESC.format(
                name_for_model=plugin_info["name_for_model"],
                name_for_human=plugin_info["name_for_human"],
                description_for_model=plugin_info["description_for_model"],
                parameters=json.dumps(plugin_info["parameters"], ensure_ascii=False),
            )
            if plugin_info.get('args_format', 'json') == 'json':
                tool += " Format the arguments as a JSON object."
            elif plugin_info['args_format'] == 'code':
                tool += ' Enclose the code within triple backticks (`) at the beginning and end of the code.'
            else:
                raise NotImplementedError
            tools_text.append(tool)
        tools_text = '\n\n'.join(tools_text)

        # 候选插件的代号
        tools_name_text = ', '.join([plugin_info["name_for_model"] for plugin_info in list_of_plugin_info])

        im_start = '<|im_start|>'
        im_end = '<|im_end|>'
        prompt = f'{im_start}system\nYou are a helpful assistant.{im_end}'
        for i, (query, response) in enumerate(chat_history):
            if list_of_plugin_info:  # 如果有候选插件
                # 倒数第一轮或倒数第二轮对话填入详细的插件信息，但具体什么位置填可以自行判断
                if (len(chat_history) == 1) or (i == len(chat_history) - 2):
                    query = PROMPT_REACT.format(
                        tools_text=tools_text,
                        tools_name_text=tools_name_text,
                        query=query,
                    )
            query = query.lstrip('\n').rstrip()  # 重要！若不 strip 会与训练时数据的构造方式产生差异。
            response = response.lstrip('\n').rstrip()  # 重要！若不 strip 会与训练时数据的构造方式产生差异。
            # 使用续写模式（text completion）时，需要用如下格式区分用户和AI：
            prompt += f"\n{im_start}user\n{query}{im_end}"
            prompt += f"\n{im_start}assistant\n{response}{im_end}"

        assert prompt.endswith(f"\n{im_start}assistant\n{im_end}")
        prompt = prompt[:-len(f'{im_end}')]
        return prompt

    def text_completion(self, input_text: str, stop_words) -> str:  # 作为一个文本续写模型来使用
        im_end = '<|im_end|>'
        if im_end not in stop_words:
            stop_words = stop_words + [im_end]
        stop_words_ids = [self.tokenizer.encode(w) for w in stop_words]

        input_ids = torch.tensor([self.tokenizer.encode(input_text)]).to(self.model.device)
        output = self.model.generate(input_ids, stop_words_ids=stop_words_ids)
        output = output.tolist()[0]
        output = self.tokenizer.decode(output, errors="ignore")
        assert output.startswith(input_text)
        output = output[len(input_text):].replace('<|endoftext|>', '').replace(im_end, '')

        for stop_str in stop_words:
            idx = output.find(stop_str)
            if idx != -1:
                output = output[:idx + len(stop_str)]
        return output  # 续写 input_text 的结果，不包含 input_text 的内容

    def parse_latest_plugin_call(self, text):
        plugin_name, plugin_args = '', ''
        i = text.rfind('\nAction:')
        j = text.rfind('\nAction Input:')
        k = text.rfind('\nObservation:')
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                # then it is likely that `Observation` is ommited by the LLM,
                # because the output text may have discarded the stop word.
                text = text.rstrip() + '\nObservation:'  # Add it back.
            k = text.rfind('\nObservation:')
            plugin_name = text[i + len('\nAction:'):j].strip()
            plugin_args = text[j + len('\nAction Input:'):k].strip()
            text = text[:k]
        return plugin_name, plugin_args, text

    def generate_with_plugin(self, history_pair: list, instruction: str):
        tools = [{
            'name_for_human': '谷歌搜索',
            'name_for_model': 'google_search',
            'description_for_model': '谷歌搜索是一个通用搜索引擎，可用于访问互联网、学习openmmlab等深度学习相关内容、查询百科知识、了解时事新闻等。',
            'parameters': [{
                'name': 'search_query',
                'description': '搜索关键词或短语',
                'required': True,
                'schema': {
                    'type': 'string'
                },
            }],
        }]
        chat_history = [(x[0], x[1]) for x in history_pair] + [(instruction, '')]

        # 需要让模型进行续写的初始文本
        planning_prompt = self.build_input_text(chat_history, tools)

        text = ''
        output = self.text_completion(planning_prompt + text, stop_words=['Observation:', 'Observation:\n'])
        action, action_input, output = self.parse_latest_plugin_call(output)
        return action, action_input, output


qwen = QwenServer()
async def inference(request):
    input_json = await request.json()
    prompt = input_json['prompt']
    history = input_json['history']
    remote = False
    if 'remote' in input_json:
        remote = input_json['remote']
    logger.info('inference {}'.format(prompt))
    text = qwen.generate_response(prompt=prompt, history=history, remote=remote)
    return web.json_response({'text': text})

app = web.Application()
app.add_routes([web.post('/inference', inference)])
web.run_app(app, host='0.0.0.0', port=9999)
