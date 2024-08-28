import openai
from openai import OpenAI


def call_openai(model_name, prompt, history):

    messages = [{
        'role': 'system',
        'content': 'You are a helpful assistant.'  # noqa E501
    }]
    for item in history:
        messages.append({'role': 'user', 'content': item[0]})
        messages.append({'role': 'system', 'content': item[1]})
    messages.append({'role': 'user', 'content': prompt})

    client = OpenAI(
        api_key='EMPTY',
        base_url='https://10.140.24.142:29500/v1',
    )

    completion = client.chat.completions.create(model=model_name,
                                                messages=messages)
    return completion.choices[0].message.content


def call2():
    from openai import OpenAI

    # Set OpenAI's API key and API base to use vLLM's API server.
    openai_api_key = 'EMPTY'
    openai_api_base = 'http://10.140.24.142:29500/v1'

    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    chat_response = client.chat.completions.create(
        model='../models/Qwen1.5-14B-Chat/',
        messages=[
            {
                'role': 'system',
                'content': 'You are a helpful assistant.'
            },
            {
                'role': 'user',
                'content': 'Tell me a joke.'
            },
        ])
    print('Chat response:', chat_response)


call2()
# call_openai("../models/Qwen1.5-14B-Chat/", '如何安装 mmdeploy', [])

# curl http://10.140.24.142:29500/v1/chat/completions \
#     -H "Content-Type: application/json" \
#     -d '{
#     "model": "../models/Qwen1.5-14B-Chat/",
#     "messages": [
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "Tell me something about large language models."}
#     ]
#     }'
