import os

from openai import OpenAI

api_key = os.getenv('STEP_API_KEY')


def test_intention_scoring():
    # 全是豆哥运行期间的真实对话
    client = OpenAI(api_key=api_key, base_url='https://api.stepfun.com/v1')

    question1 = '请用四字成语形容一个人皮肤光滑，就像渲染里开了抗锯齿。'
    question2 = '“不是盲审嘛，这对其他工作不太公平吧”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question3 = '“矩阵乘法有问题，我这段时间跑的模型怕不是都白跑了”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question4 = '“你这次卧还带玄关 真好”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question5 = '“我好气啊，为啥我赚不到这个钱”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question6 = '“要不，还是把豆哥从卷卷群移除吧”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
    question7 = '检查英文表达是否合适：Web portal is available on [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), you can build your own knowledge assistant, zero coding with WeChat and Feishu group.'
    # ChatCompletionMessage(content='The English expression is mostly suitable, but there are a few minor issues:\n\n1. "available" should be "available".\n2. "zero coding" is a bit informal and may not be understood by all readers. A more formal alternative could be "without any coding experience required".\n3. "WeChat and Feishu group" should be "WeChat and Feishu groups".\n\nHere\'s the corrected version:\n\n"The web portal is available on [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), where you can build your own knowledge assistant without any coding experience required, using WeChat and Feishu groups."', role='assistant', function_call=None, tool_calls=None)

    questions = [question7]

    for question in questions:
        completion = client.chat.completions.create(
            model='step-1',
            temperature=0.2,
            messages=[
                {
                    'role':
                    'system',
                    'content':
                    '你是由阶跃星辰提供的AI聊天助手，你擅长中文，英文，以及多种其他语言的对话。在保证用户数据安全的前提下，你能对用户的问题和请求，作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容',
                },
                {
                    'role': 'user',
                    'content': question
                },
            ],
        )

        # 光滑如玉
        # 肤如凝脂。这句成语形容人的皮肤光滑、细腻，如同凝固的油脂一般，与你描述的开了抗锯齿的效果相符合。
        # 'The model "step-1-200k" does not exist or you do not have access to it.'  for step-1-200k
        # 直接给 step-1 也对
        print(question)
        print(completion.choices[0].message)


def test_multimodal():
    question1 = (
        '这个截图里在说什么？',
        'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/inside-mmpose.jpg'
    )
    # ChatCompletionMessage(content='在您上传的微信群聊截图中，用户“茵香豆”询问了有关MMPose中FLW数据集的官方标注JSON文件中的“scale”是如何计算出来的问题。随后，“茵
    # 香豆”表示感谢，提到了“发红包怎么写的你的账户受限”，并惊讶地发现“不可能，他是机器人”。最后，“茵香豆”说“豆哥出息了，挣到猫粮了”，并配了一张图片。对话中还出现了
    # 一张“豆哥”的表情包图片。整个对话气氛轻松幽默。', role='assistant', function_call=None, tool_calls=None)

    question2 = (
        '提取图片里的对话，结果用 json 表示。直接告诉我 json 结果，不要解释',
        'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/inside-ncnn-group.jpg'
    )

    # ChatCompletionMessage(content='```json\n{\n  "type": "对话",\n  "title": "TP除了gather reduce broadcast还有啥",\n  "content": "还有allreduce、allgather、reducescatter",\n  "source": "茴香豆"\n}\n```', role='assistant', function_call=None, tool_calls=None)

    question3 = (
        '回答这个截图里，第一条用户的问题。直接回答问题本身，不要解释，不要告诉我问题是什么。',
        'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/inside-mmpose.jpg'
    )
    # ChatCompletionMessage(content='在MMPose中，WFLW数据集的官网标注JSON文件中的“scale”是根据图像的原始尺寸和处理后的尺寸计算出来的。具体来说，“scale”是将图像缩放
    # 到用于训练或测试的固定分辨率（例如，固定的分辨率）时的缩放因子。', role='assistant', function_call=None, tool_calls=None)

    question4 = (
        '图片里是什么群的二维码？干什么用的。不要解释，直接告诉我答案。',
        'https://huixiangdou-data.oss-cn-shanghai.aliyuncs.com/wechat.jpg')
    # ChatCompletionMessage(content='图片中的二维码是“openmmlab 茴香豆（惊蛰）”群的二维码。这个群组的名称可能与一个名为“openmmlab”的项目或组织有关，而“茴香豆”和“惊
    # 蛰”可能是群组的昵称或特定于该群的内部代号。由于我无法直接访问二维码背后的信息，我无法提供关于该群具体目的的详细信息。', role='assistant', function_call=None, tool_calls=None)

    questions = [question4]

    client = OpenAI(api_key=api_key, base_url='https://api.stepfun.com/v1')

    for question in questions:
        completion = client.chat.completions.create(
            model='step-1v-32k',
            temperature=0.2,
            messages=[
                {
                    'role':
                    'system',
                    'content':
                    '你是由阶跃星辰提供的AI聊天助手，你除了擅长中文，英文，以及多种其他语言的对话以外，还能够根据用户提供的图片，对内容进行精准的内容文本描述。在保证用户数据安全的前提下，你能对用户的问题和请求，作出快速和精准的回答。同时，你的回答和建议应该拒绝黄赌毒，暴力恐怖主义的内容',
                },
                {
                    'role': 'user',
                    'content': '你好呀!'
                },
                {
                    'role':
                    'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': question[0],
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': question[1]
                            },
                        },
                    ],
                },
            ],
        )

        print(completion.choices[0].message)


test_intention_scoring()
# test_multimodal()
