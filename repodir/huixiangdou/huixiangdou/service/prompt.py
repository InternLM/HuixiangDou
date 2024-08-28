# PreprocNode
SCORING_QUESTION_TEMPLTE_CN = '“{}”\n请仔细阅读以上内容，判断句子是否是个有主题的疑问句，结果用 0～10 表示。直接提供得分不要解释。\n判断标准：有主语谓语宾语并且是疑问句得 10 分；缺少主谓宾扣分；陈述句直接得 0 分；不是疑问句直接得 0 分。直接提供得分不要解释。'
CR_NEED_CN = """群聊场景中“这”、“它”、“哪”等代词需要查看上下文和其他用户的回复才能确定具体指什么，请完成群聊场景代词替换任务。
以下是历史对话，可能有多个人的发言：
{}
输入内容：{}
输入内容的信息是否完整，是否需要从历史对话中提取代词或宾语来替代 content 中的一部分词汇？ A：不需要提取，信息完整  B：需要  C：不知道
一步步分析，首先历史消息包含哪些话题；其次哪个话题与问题最相关；如果都不相关就不提取。"""
CR_CN = """请根据历史对话，重写输入的文本。
以下是历史对话，可能有多个人的发言：
{}
输入的文本
“{}”
一步步分析，首先历史对话包含哪些话题；其次哪个话题与输入文本中的代词最相关；用相关的话题，替换输入中的代词和缺失的部分。直接返回重写后的文本不要解释。"""

SCORING_QUESTION_TEMPLTE_EN = '"{}"\nPlease read the content above carefully and judge whether the sentence is a thematic question. Rate it on a scale of 0-10. Only provide the score, no explanation.\nThe criteria are as follows: a sentence gets 10 points if it has a subject, predicate, object and is a question; points are deducted for missing subject, predicate or object; declarative sentences get 0 points; sentences that are not questions also get 0 points. Just give the score, no explanation.'
CR_NEED_EN = """In group chat scenarios, pronouns such as "this," "it," and "which" require examination of the context and other users' responses to determine their specific reference. Please complete the pronoun substitution task in the group chat scenario.
Here is the historical conversation, which may contain multiple people's statements:
{}
Input content: {}
Is the information in the input content complete, and is it necessary to extract pronouns or objects from the historical conversation to replace part of the vocabulary in content? A: No extraction needed, information is complete B: Necessary C: Uncertain
Analyze step by step, first identify which topics are included in the historical messages; second, determine which topic is most relevant to the question; if none are relevant, do not extract."""
CR_EN = """Please rewrite the input text based on the historical conversation.
Here is the historical conversation, which may include statements from multiple individuals:
{}
The input text
"{}"
Analyze step by step, first identify what topics are included in the historical conversation; secondly, determine which topic is most relevant to the pronoun in the input text; replace the pronoun and missing parts in the input with the relevant topic. Return the rewritten text directly without explanation."""

# Text2vecNode
TOPIC_TEMPLATE_CN = '告诉我这句话的主题，不要丢失主语和宾语，直接说主题不要解释：“{}”'
SCORING_RELAVANCE_TEMPLATE_CN = '问题：“{}”\n材料：“{}”\n请仔细阅读以上内容，判断问题和材料的关联度，用0～10表示。判断标准：非常相关得 10 分；完全没关联得 0 分。直接提供得分不要解释。\n'  # noqa E501
GENERATE_TEMPLATE_CN = '材料：“{}”\n 问题：“{}” \n 请仔细阅读参考材料回答问题。'  # noqa E501

TOPIC_TEMPLATE_EN = 'Tell me the theme of this sentence, just state the theme without explanation: "{}"'  # noqa E501
SCORING_RELAVANCE_TEMPLATE_EN = 'Question: "{}", Background Information: "{}"\nPlease read the content above carefully and assess the relevance between the question and the material on a scale of 0-10. The scoring standard is as follows: extremely relevant gets 10 points; completely irrelevant gets 0 points. Only provide the score, no explanation needed.'  # noqa E501
GENERATE_TEMPLATE_EN = 'Background Information: "{}"\n Question: "{}"\n Please read the reference material carefully and answer the question.'  # noqa E501

# WebSearchNode
KEYWORDS_TEMPLATE_CN = '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。搜索参数类型 string， 内容是短语或关键字，以空格分隔。\n你现在是{}交流群里的助手，用户问“{}”，你打算通过谷歌搜索查询相关资料，请提供用于搜索的关键字或短语，不要解释直接给出关键字或短语。'  # noqa E501
KEYWORDS_TEMPLATE_EN = 'Google search is a general-purpose search engine that can be used to access the internet, look up encyclopedic knowledge, keep abreast of current affairs and more. Search parameters type: string, content consists of phrases or keywords separated by spaces.\nYou are now the assistant in the "{}" communication group. A user asked "{}", you plan to use Google search to find related information, please provide the keywords or phrases for the search, no explanation, just give the keywords or phrases.'  # noqa E501

# SecurityNode
PERPLESITY_TEMPLATE_CN = '“question:{} answer:{}”\n阅读以上对话，answer 是否在表达自己不知道，回答越全面得分越少，用0～10表示，不要解释直接给出得分。\n判断标准：准确回答问题得 0 分；答案详尽得 1 分；知道部分答案但有不确定信息得 8 分；知道小部分答案但推荐求助其他人得 9 分；不知道任何答案直接推荐求助别人得 10 分。直接打分不要解释。'  # noqa E501
SECURITY_TEMAPLTE_CN = '判断以下句子是否涉及政治、辱骂、色情、恐暴、宗教、网络暴力、种族歧视等违禁内容，结果用 0～10 表示，不要解释直接给出得分。判断标准：涉其中任一问题直接得 10 分；完全不涉及得 0 分。直接给得分不要解释：“{}”'  # noqa E501
PERPLESITY_TEMPLATE_EN = 'Question: {} Answer: {}\nRead the dialogue above, does the answer express that they don\'t know? The more comprehensive the answer, the lower the score. Rate it on a scale of 0-10, no explanation, just give the score.\nThe scoring standard is as follows: an accurate answer to the question gets 0 points; a detailed answer gets 1 point; knowing some answers but having uncertain information gets 8 points; knowing a small part of the answer but recommends seeking help from others gets 9 points; not knowing any of the answers and directly recommending asking others for help gets 10 points. Just give the score, no explanation.'  # noqa E501
SECURITY_TEMAPLTE_EN = 'Evaluate whether the following sentence involves prohibited content such as politics, insult, pornography, terror, religion, cyber violence, racial discrimination, etc., rate it on a scale of 0-10, do not explain, just give the score. The scoring standard is as follows: any violation directly gets 10 points; completely unrelated gets 0 points. Give the score, no explanation: "{}"'  # noqa E501
