# python3
# Test MiniMax LLM API via OpenAI-compatible interface
# Usage: MINIMAX_API_KEY=your_key python3 tests/test_minimax.py
import os
from openai import OpenAI

api_key = os.environ.get('MINIMAX_API_KEY', '')
if not api_key:
    print('Please set MINIMAX_API_KEY environment variable')
    exit(1)

client = OpenAI(api_key=api_key, base_url='https://api.minimax.io/v1')
queries = [
    'What is the full name of ncnn, given that cnn stands for Convolutional Neural Network and n is for nihui, the author of ncnn?',
    '"How to install mmdeploy?"\nPlease read the above carefully and determine if it is a question with a clear topic. Rate it from 0 to 10. Provide only the score without explanation.\nCriteria: 10 points for a question with subject, verb, and object; deduct for missing components; 0 for declarative sentences or non-questions.',
]

for query in queries:
    response = client.chat.completions.create(
        model='MiniMax-M1',
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
        temperature=0.7)

    print(response.choices[0].message.content)
