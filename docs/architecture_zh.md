# 代码结构说明

本文主要解释豆哥（茴香豆）各目录和功能。文档可能无法随代码即时更新，但已有定义不会再变动。

## 第一层：项目介绍

项目最外层，只有 huixiangdou python module 和 1 个配置文件。

```bash
.
├── config-advanced.ini
├── config-2G.ini # 高级版和体验版配置范例，轻微修改了 `config.ini`
├── config.ini      # 基础配置范例，包含算法所有选项和参数
..
├── huixiangdou     # python module
..
├── requirements-lark-group.txt  # 集成飞书群才需要的依赖
├── requirements.txt  # 基础依赖
```

配置实际是 toml 格式，为了避免用户觉得陌生，改名 windows 常见的 .ini

## 第二层：huixiangdou module

module 内只有 3 个部分：

```bash
.
├── frontend       # 飞书、微信这些，都是茴香豆算法的前端
├── main.py        #  main 提供示例程序
├── service        # service 就是算法实现
```

**service** 我们在[论文](https://arxiv.org/abs/2401.08772)里介绍豆哥是套 pipeline。在实现里，可能包含函数、本地 LLM 或者 RPC。把这些基础能力都视做 service。

**frontend** 既然豆哥是套算法 pipeline，那么微信、飞书、web 这些，都是它的前端。这个目录放调用前端的工具类和函数，目前里面是飞书的 API 用法

**main.py** 现在有算法、有前端，需要个入口函数实现业务逻辑。你在 `config.ini` 配置了飞书，就应该发给飞书 qaq

## 第三层：service

这里是茴香豆算法主体。

```bash
.
├── feature_store.py # 管理文本特征的建立和查询，未来会把 “建立” 和 “查询” 分开
├── helper.py        # 放一些辅助工具
├── llm_client.py    # LLM 可能是个 RPC，所以需要个 client
├── llm_server_hybrid.py  # LLM 可能不止一个，所以是 hybrid
├── sg_search.py     # sourcegraph 客户端
├── web_search.py    # google search 的客户端
└── worker.py        # 论文所说的主逻辑，调用上面的组件
```

**1. feature_store.py** 人脸识别时代，面部特征的存储和检索叫 feature_store，这是名字来源。

1. 提取特征时，会花式分割文本（构造技巧会影响精度）、text2vec 模型提取特征、保存到本地；
2. 检索时，除了直接用 text2vec 匹配，还会 rerank 模型调整顺序

feature_store 在整个 pipeline 里仅仅是 “引路牌” 的作用，并不依赖 chunk 作答。

**2. llm 部分** 包含了 client 和 server_hybrid，是因为：

1. 模型可能部署在本地，也可以是 openai 接口
2. 每个模型的特色不同，我们既希望便宜，又不想少功能。所以就是“按需调用”，因此得名 `hybrid`
3. 同样的 `topk=1` 功能，但每家的配置参数不一样，主逻辑不管这些细节，都实现在 `llm_server_hybrid.py`

**3. 搜索** LLM 作答总需要个 ground truth，如果知识库提供不了，依赖搜索引擎是个不错的选择。这里的特色是：**反复检查网络结果的质量**。网上的信息大都有害，不过滤就直接用，轻则回答错误；重则价值观问题

**4. 搜索增强 sg_search** 引擎的搜索能力有限，而浩瀚知识是无限的，“海底捞针” 当然艰难。

但如果事先知道答案就在某个 repo 里，只搜那个 repo，必然能提升精度。 `sg_search` 就是针对一个小 repo 调用知识图谱找答案，“大炮打蚊子” 往往效果不错。

**5. 主逻辑 worker.py** 在多个微信群运行半年，被“攻击”数万次后，总结出的一套 pipeline
