# python3
from openai import OpenAI

client = OpenAI(api_key='sk-f58e45ee054743f898f732b09dbcaa7c',
                base_url='https://api.deepseek.com/v1')
queries = [
    '已知 ncnn 中 cnn 是卷积神经网络，n 是 ncnn 的作者 nihui。所以 ncnn 的全称是？',
    '"请问如何安装 mmdeploy ?"\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。',
    '"豆哥少水点键证群"\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
]

for query in queries:
    response = client.chat.completions.create(
        model='deepseek-chat',
        messages=[
            {
                'role': 'system',
                'content': 'You are a helpful assistant'
            },
            {
                'role': 'user',
                'content': query
            },
        ],
        temperature=0.1)

    print(response.choices[0].message.content)
