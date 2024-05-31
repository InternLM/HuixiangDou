import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv('MOONSHOT_API_KEY'),
    base_url='https://api.moonshot.cn/v1',
)

prompt = "“huixiangdou 是什么？”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。"

def generate():
    """Test generate."""
    messages = [{
        'role':
        'system',
        'content':
        '你是一个语文专家，擅长对句子的结构进行分析'
        # '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。
        # 同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'
    }, {
        'role': 'user',
        'content': prompt
    }]

    whole_input = str(messages)
    print(whole_input)
    # print('input_length {}'.format(len(whole_input)))

    try:
        completion = client.chat.completions.create(
            model='moonshot-v1-8k',
            messages=messages,
            temperature=0.1,
            n = 10
        )
    except Exception as e:
        return prompt, str(e)
    
    results = []
    for choice in completion.choices:
        results.append(choice.message.content)

    return prompt, results

if __name__ == '__main__':
    print(generate())
