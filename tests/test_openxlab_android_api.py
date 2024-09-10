import requests
import json
import time

# 定义要发送的数据
data = {
    "query_id": "random_string_for_log_analysis",  # 自己定义的随机 str，用来 async 映射谁是谁的消息
    "groupname": "茴香豆（大暑群）",  # 群名
    "username": "tpoisonooo", # 微信群中的用户名
    "query": {
        "type": "text",  # 类型，支持 text 和 poll 两种。 text 意味上行给服务器发消息； poll 意味着拉**所有历史** chat 结果。
        "content": "你好，请问如何安装 mmpose ?" # 群里发的问题
    }
}

# 输出样例
# {
#   "msg": "ok",
#   "msgCode": "10000",
#   "data": [
#     {
#       "req": {
#         "query_id": "random_string_for_log_analysis",
#         "groupname": "茴香豆（大暑群）",
#         "username": "tpoisonooo",
#         "query": {
#           "type": "text",
#           "content": "你好，请问如何安装 mmpose ?"
#         }
#       },
#       "rsp": {
#         "code": 15,
#         "state": "Web search fail, please check network, TOKEN and quota",
#         "text": "根据提供的材料，HuixiangDou 是一个基于大型语言模型（LLM）的技术助手，旨在帮助算法开发者回答与开源算法项目相关的问题，例如计算机视觉和深度学习项目。这个系统被设计成可以集成到即时通讯工具（如微信和飞书）的群聊中，以提供技术支持。\n\n为了回答用户的问题，HuixiangDou 会首先通过其拒绝管道（Reject Pipeline）来确定这个问题是否值得回答。如果问题与技术相关，它将通过响应管道（Response Pipeline）来寻找答案。在这个过程中，系统会使用关键词提取、文档片段搜索和 LLM 评分等技术来确保答案的准确性和相关性。\n\n因此，对于用户提出的问题“你好，请问如何安装 mmpose ?”，HuixiangDou 会首先判断这个问题是否与技术相关，如果是，它将尝试从其知识库中搜索相关信息，并提供一个基于 LLM 的响应来指导用户如何安装 mmpose。\n\n请注意，由于 HuixiangDou 是一个技术助手，它可能无法提供非常详细的安装步骤，但它应该能够提供一些基本的指导和建议，帮助用户开始安装过程。如果需要更具体的帮助，用户可能需要参考 mmpose 的官方文档或寻求社区支持。",
#         "references": []
#       }
#     },
#     {
#       "req": {
#         "query_id": "random_string_for_log_analysis",
#         "groupname": "茴香豆（大暑群）",
#         "username": "tpoisonooo",
#         "query": {
#           "type": "text",
#           "content": "你好，请问如何安装 mmpose ?"
#         }
#       },
#       "rsp": {
#         "code": 15,
#         "state": "Web search fail, please check network, TOKEN and quota",
#         "text": "根据提供的材料，HuixiangDou 是一个基于大型语言模型（LLM）的技术助手，旨在帮助算法开发者回答与开源算法项目相关的问题，例如计算机视觉和深度学习项目。这个系统被设计成可以集成到即时通讯工具（如微信和飞书）的群聊中，以提供技术支持。\n\n为了回答用户的问题，HuixiangDou 会首先通过其拒绝管道（Reject Pipeline）来确定这个问题是否值得回答。如果问题与技术相关，它将通过响应管道（Response Pipeline）来寻找答案。在这个过程中，系统会使用关键词提取、文档片段搜索和 LLM 评分等技术来确保答案的准确性和相关性。\n\n因此，对于用户提出的问题“你好，请问如何安装 mmpose ?”，HuixiangDou 会首先判断这个问题是否与技术相关，如果是，它将尝试从其知识库中搜索相关信息，并提供一个基于 LLM 的响应来指导用户如何安装 mmpose。\n\n请注意，由于 HuixiangDou 是一个技术助手，它可能无法提供非常详细的安装步骤，但它应该能够提供一些基本的指导和建议，帮助用户开始安装过程。如果需要更具体的帮助，用户可能需要参考 mmpose 的官方文档或寻求社区支持。",
#         "references": []
#       }
#     }
#   ]
# }

# 指定API的URL
url = "http://139.224.198.162:18443/api/v1/message/v1/wechat/3Cy7"  # 请替换为实际的API URL

# 设置请求头，通常需要包含Content-Type为application/json
headers = {
    'Content-Type': 'application/json'
}

# 发送POST请求
response = requests.post(url, data=json.dumps(data), headers=headers)

# 打印响应的状态码和内容
print("Status Code:", response.status_code)
print("Response Body:", response.text)

for i in range(60):
    print("waiting for reply")
    data['query']['type'] = 'poll'
    response = requests.post(url, data=json.dumps(data), headers=headers)
    json_obj = json.loads(response.text)

    resp_data = json_obj['data']
    if len(resp_data) > 0:
        print(response.text)
        break
    else:
        print(resp_data)

    time.sleep(2)

