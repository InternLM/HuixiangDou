import tiktoken
import re

ENCODER = None

# modified from https://github.com/HKUDS/LightRAG
def encode_string(content: str, model_name: str = "gpt-4o"):
    global ENCODER
    if ENCODER is None:
        tiktoken.get_encoding("cl100k_base")
        ENCODER = tiktoken.encoding_for_model(model_name)
    tokens = ENCODER.encode(content)
    return tokens


def decode_tokens(tokens: list[int], model_name: str = "gpt-4o"):
    global ENCODER
    if ENCODER is None:
        ENCODER = tiktoken.encoding_for_model(model_name)
    content = ENCODER.decode(tokens)
    return content


ZH_CN_CHAR_PATTERN = None
EN_CHAR_PATTERN = None


def judge_language(text):
    # 计算中文字符的数量
    global ZH_CN_CHAR_PATTERN
    if ZH_CN_CHAR_PATTERN is None:
        ZH_CN_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')

    global EN_CHAR_PATTERN
    if EN_CHAR_PATTERN is None:
        EN_CHAR_PATTERN = re.compile(r'[a-zA-Z]')

    chinese_count = len(ZH_CN_CHAR_PATTERN.findall(text))
    english_count = len(EN_CHAR_PATTERN.findall(text))

    # 判断中英文的比例
    if chinese_count > english_count:
        return "zh_cn"
    else:
        return "en"