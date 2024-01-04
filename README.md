# HuixiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance

<small> 简体中文 | [English](README_en.md) </small>

[![GitHub license](https://img.shields.io/badge/license-BSD--3--Clause-brightgreen.svg)](./LICENSE)
![CI](https://img.shields.io/github/actions/workflow/status/internml/huixiangdou/lint.yml?branch=master)

“茴香豆”是一个基于 LLM 的领域特定知识助手。特点：
1. 应对群聊这类复杂场景，解答用户问题的同时，不会消息泛滥
2. 提出一套解答技术问题的算法 pipeline
3. 部署成本低，只需要 LLM 模型满足 4 个 trait 即可解答大部分用户问题，见[技术报告](./resource/HuixiangDou.pdf)

查看[茴香豆已运行在哪些场景](./huixiangdou-inside.md)。

# 🔥 运行

我们将以 lmdeploy & mmpose 为例，介绍如何把知识助手部署到飞书群

## STEP1. 建立话题特征库
```bash
# 下载聊天话题
mkdir repodir
git clone https://github.com/openmmlab/mmpose --depth=1 repodir/mmpose
git clone https://github.com/internlm/lmdeploy --depth=1 repodir/lmdeploy

# 建立特征库
cd HuixiangDou && mkdir workdir # 创建工作目录
python3 -m pip install -r requirements.txt # 安装依赖
python3 service/feature_store.py repodir workdir # 把 repodir 的特征保存到 workdir
```
运行结束后，茴香豆能够区分应该处理哪些用户话题，哪些闲聊应该拒绝。请编辑 [good_questions](./resource/good_questions.json) 和 [bad_questions](./resource/bad_questions.json)，尝试自己的领域知识（医疗，金融，电力等）。

```bash
# 接受技术话题
process query: mmdeploy 现在支持 mmtrack 模型转换了么
process query: 有啥中文的 text to speech 模型吗?
# 拒绝闲聊
reject query: 今天中午吃什么？
reject query: 茴香豆是怎么做的
```

## STEP2. 运行基础版技术助手

**配置免费 TOKEN**

茴香豆使用了搜索引擎，点击 [serper 官网](https://serper.dev/api-key)获取限额 WEB_SEARCH_TOKEN，填入 `config.ini`

```shell
# config.ini
..
[web_search]
x_api_key = "${YOUR-X-API-KEY}"
..
```

**测试问答效果**

请保证 GPU 显存超过 20GB（如 3090 及以上），若显存较低请按 FAQ 修改。

首次运行将自动下载配置中的 internlm2-7B 和 text2vec-large-chinese，请保证网络畅通。

  * **非 docker 用户**。如果你**不**使用 docker 环境，可以一次启动所有服务。
    ```bash
    # standalone
    python3 main.py workdir --standalone
    ..
    ErrorCode.SUCCESS, 要安装 MMDeploy，首先需要准备一个支持 Python 3.6+ 和 PyTorch 1.8+ 的环境。然后，可以通过以下步骤安装 MMDeploy..
    ```

  * **docker 用户**。如果你正在使用 docker，`HuixiangDou` 的 Hybrid LLM Service 分离部署。
    ```bash
    # 启动服务
    python3 service/llm_server_hybride.py
    ```
    打开新终端，把 host IP 配置进 `config.ini`，运行

    ```bash
    # config.ini
    [llm]
    ..
    client_url = "http://10.140.24.142:39999/inference" # 举例

    python3 main.py workdir
    ```

## STEP3.集成到飞书[可选]

点击[创建飞书自定义机器人](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)，获取回调 WEBHOOK_URL，填写到 config.ini

```shell
# config.ini
..
[frontend]
type = "lark"
webhook_url = "${YOUR-LARK-WEBHOOK-URL}"
```

运行。结束后，技术助手的答复将发送到飞书群。
```shell
python3 main.py workdir
```
<img src="./resource/figures/lark-example.png" width="400">

如果还需要读取飞书群消息，见[飞书开发者广场-添加应用能力-机器人](https://open.feishu.cn/app?lang=zh-CN)。

## STEP4.高精度配置[可选]
为了进一步提升助手的答复体验，以下特性，开启得越多越好。

1. 使用更高精度 local LLM

    把 config.ini 中的`llm.local` 模型调整为 `internlm2-20B`
    此选项效果显著，但需要更大的 GPU 显存。

2. Hybrid LLM Service

    对于支持 openai 接口的 LLM 服务，茴香豆可以发挥它的 Long Context 能力。
    以 kimi 为例，以下是 `config.ini` 配置示例：

    ```bash
    # config.ini
    [llm.server]
    ..
    # open https://platform.moonshot.cn/
    remote_type = "kimi"
    remote_api_key = "YOUR-KIMI-API-KEY"
    remote_llm_max_text_length = 128000
    remote_llm_model = "moonshot-v1-128k"
    ```
    我们同样支持 gpt API。注意此特性会增加响应耗时和运行成本。

3. repo 搜索增强

    此特性适合处理疑难问题，需要基础开发能力调整 prompt。

    * 点击 [sourcegraph-settings-access](https://sourcegraph.com/users/tpoisonooo/settings/tokens) 获取 token

        ```bash
        # open https://github.com/sourcegraph/src-cli#installation
        curl -L https://sourcegraph.com/.api/src-cli/src_linux_amd64 -o /usr/local/bin/src && chmod +x /usr/local/bin/src

        # 把 token 填入 config.ini
        [sg_search]
        ..
        src_access_token = "${YOUR_ACCESS_TOKEN}"
        ```
    
    * 编辑 repo 的名字和简介，我们以 opencompass 为例

        ```bash
        # config.ini
        # add your repo here, we just take opencompass and lmdeploy as example
        [sg_search.opencompass]
        github_repo_id = "open-compass/opencompass"
        introduction = "用于评测大型语言模型（LLM）.."
        ```
    
    * 使用 `python3 service/sg_search.py` 单测，返回内容应包含 opencompass 源码和文档
  
       ```bash
       python3 service/sg_search.py
       ..
       "filepath": "opencompass/datasets/longbench/longbench_trivia_qa.py",
       "content": "from datasets import Dataset..
       ```

    运行 `main.py`，茴香豆将在合适的时机，启用搜索增强。


# 🛠️ FAQ 

1. 如何接入其他 IM ？
    * 微信。企业微信请查看[企业微信应用开发指南](https://developer.work.weixin.qq.com/document/path/90594)；对于个人微信，我们已向微信团队确认暂无 API，须自行搜索学习
    * 钉钉。参考[钉钉开放平台-自定义机器人接入](https://open.dingtalk.com/document/robots/custom-robot-access)

2. 机器人太高冷/太嘴碎怎么办？

    * 把真实场景中，把应该回答的问题填入`resource/good_questions.json`，应该拒绝的填入`resource/bad_questions.json`
    * 调整 `repodir` 中的主题内容，确保底库的 markdown 文档不包含场景无关内容

    重新执行 `service/feature_store.py`，更新阈值和特征库

3. 启动正常，但运行期间显存 OOM 怎么办？

    基于 transformers 结构的 LLM 长文本需要更多显存，此时需要对模型做 kv cache 量化，如 [lmdeploy 量化说明](https://github.com/InternLM/lmdeploy/blob/main/docs/en/kv_int8.md)。然后使用 docker 独立部署 Hybrid LLM Service。

4. 如何接入其他 local LLM/ 接入后效果不理想怎么办？

    * 打开 [hybrid llm service](./service/llm_server_hybrid.py)，增加新的 LLM 推理实现
    * 参照 [test_intention_prompt 和测试数据](./tests/test_intention_prompt.py)，针对新模型调整 prompt 和阈值，更新到 [worker.py](./service/worker.py)

5. 响应太慢/请求总是失败怎么办？

    * 参考 [hybrid llm service](./service/llm_server_hybrid.py) 增加指数退避重传
    * local LLM 替换为 [lmdeploy](https://github.com/internlm/lmdeploy) 等推理框架，而非原生的 huggingface/transformers
      
5. GPU 显存太低怎么办？

    此时无法运行 local LLM，只能用 remote LLM 配合 text2vec 执行 pipeline。请确保 `config.ini` 只使用 remote LLM，关闭 local LLM

# 📝 License
项目使用 [BSD 3-Clause License](./LICENSE)
