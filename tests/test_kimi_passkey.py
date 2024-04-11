import argparse
import os

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv('MOONSHOT_API_KEY'),
    base_url='https://api.moonshot.cn/v1',
)


def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--max_tokens',
                        type=int,
                        default=782000,
                        help='maximum token length for evaluation')
    parser.add_argument('--num_tests',
                        type=int,
                        default=1,
                        help='number of repeat testing for each length')

    args = parser.parse_args()
    return args


def generate(prompt: str):
    """Test generate."""
    messages = [{
        'role':
        'system',
        'content':
        '你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一些涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。'
    }, {
        'role': 'user',
        'content': prompt
    }]

    # whole_input = str(messages)
    # print('input_length {}'.format(len(whole_input)))

    try:
        completion = client.chat.completions.create(
            model='moonshot-v1-128k',
            messages=messages,
            temperature=0.3,
        )
    except Exception as e:
        return prompt, str(e)
    # print(completion.choices)
    return prompt, completion.choices[0].message.content


# copy from https://github.com/dvlab-research/LongLoRA/blob/main/passkey_retrivial.py
def generate_prompt_landmark(n_garbage=60000, seed=666):
    """Generates a text file and inserts an passkey at a random position."""
    from numpy import random
    rnd_state = random.get_state()
    random.seed(seed)
    n_garbage_prefix = random.randint(0, n_garbage)
    n_garbage_suffix = n_garbage - n_garbage_prefix

    task_description = 'There is an important info hidden inside a lot of irrelevant text. Find it and memorize them. I will quiz you about the important information there.'
    garbage = 'The grass is green. The sky is blue. The sun is yellow. Here we go. There and back again.'
    garbage_inf = ' '.join([garbage] * 384000)
    assert len(garbage_inf) >= n_garbage
    garbage_prefix = garbage_inf[:n_garbage_prefix]
    garbage_suffix = garbage_inf[:n_garbage_suffix]
    pass_key = random.randint(1, 192000)
    information_line = f'The pass key is {pass_key}. Remember it. {pass_key} is the pass key.'
    final_question = 'What is the pass key? The pass key is'
    lines = [
        task_description,
        garbage_prefix,
        information_line,
        garbage_suffix,
        final_question,
    ]
    random.set_state(rnd_state)
    return '\n'.join(lines), str(pass_key)


def main(args):
    n_garbage = args.max_tokens - 1000
    passed_tests = 0
    for j in range(args.num_tests):
        prompt, pass_key = generate_prompt_landmark(n_garbage=n_garbage,
                                                    seed=5120 + j)

        try:
            response = generate(prompt='hello')
            print(response)
            response = generate(prompt=prompt)
        except Exception as e:
            print(e)
        print('result: ', response, pass_key)

        if pass_key in response.content:
            passed_tests += 1

    precision = passed_tests / args.num_tests
    print('precision {} @ {}'.format(precision, args.max_tokens))


if __name__ == '__main__':
    args = parse_config()
    main(args)
