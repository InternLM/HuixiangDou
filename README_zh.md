<div align="center">
  <img src="resource/logo_blue.svg" width="550px"/>

<small> 简体中文 | [English](README.md) </small>

[![GitHub license](https://img.shields.io/badge/license-BSD--3--Clause-brightgreen.svg?style=plastic)](./LICENSE)
[![pypi](https://img.shields.io/badge/install-PyPI-green.svg?style=plastic)](https://pypi.org/project/huixiangdou/)
![CI](https://img.shields.io/github/actions/workflow/status/internml/huixiangdou/lint.yml?branch=master&style=plastic)

</div>

“茴香豆”是一个基于 LLM 的领域知识助手。特点：

1. 应对群聊这类复杂场景，解答用户问题的同时，不会消息泛滥
2. 提出一套解答技术问题的算法 pipeline
3. 部署成本低，只需要 LLM 模型满足 4 个 trait 即可解答大部分用户问题，见[技术报告](./resource/HuixiangDou.pdf)

查看[茴香豆已运行在哪些场景](./huixiangdou-inside.md)，加入[微信群](./resource/figures/wechat.jpg)体验最新版效果。

# 📦 硬件要求

以下是运行茴香豆的硬件需求。建议遵循部署流程，从基础版开始，逐渐体验高级特性。

|  版本  | GPU显存需求 |                            描述                            |                             Linux 系统已验证设备                              |
| :----: | :---------: | :--------------------------------------------------------: | :---------------------------------------------------------------------------: |
| 基础版 |    22GB     |            能回答领域知识的基础问题，零成本运行            | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
| 高级版 |    40GB     |               能够回答源码级问题，零成本运行               | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |
| 魔改版 |     4GB     | 用 openai API 替代本地 LLM，处理源码级问题。需要开发能力，运行需要费用 | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |

# 🔥 运行

我们将以 lmdeploy & mmpose 为例，介绍如何把知识助手部署到飞书群

## STEP1. 建立话题特征库

复制下面所有命令（包含 '#' 符号）执行。

```shell
# 下载 repo
git clone https://github.com/internlm/huixiangdou --depth=1 && cd huixiangdou

# 下载聊天话题
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1 repodir/mmpose
git clone https://github.com/internlm/lmdeploy --depth=1 repodir/lmdeploy

# 建立特征库
mkdir workdir # 创建工作目录
python3 -m pip install -r requirements.txt # 安装依赖，若 python3.11 则需要 `conda install conda-forge::faiss-gpu`
python3 -m huixiangdou.service.feature_store # 把 repodir 的特征保存到 workdir
```

首次运行将自动下载配置中的 [text2vec-large-chinese](https://huggingface.co/GanymedeNil/text2vec-large-chinese)。考虑到不同地区 huggingface 连接问题，建议先手动下载到本地，然后在 `config.ini` 设置模型路径。例如：

```shell
# config.ini
[feature_store]
..
model_path = "/path/to/text2vec-large-chinese"
```

运行结束后，茴香豆能够区分应该处理哪些用户话题，哪些闲聊应该拒绝。请编辑 [good_questions](./resource/good_questions.json) 和 [bad_questions](./resource/bad_questions.json)，尝试自己的领域知识（医疗，金融，电力等）。

```shell
# 接受技术话题
process query: mmdeploy 现在支持 mmtrack 模型转换了么
process query: 有啥中文的 text to speech 模型吗?
# 拒绝闲聊
reject query: 今天中午吃什么？
reject query: 茴香豆是怎么做的
```

## STEP2. 运行基础版技术助手

**配置免费 TOKEN**

茴香豆使用了搜索引擎，点击 [Serper 官网](https://serper.dev/api-key)获取限额 TOKEN，填入 `config.ini`

```shell
# config.ini
..
[web_search]
x_api_key = "${YOUR-X-API-KEY}"
..
```

**测试问答效果**

请保证 GPU 显存超过 22GB（如 3090 及以上），若显存较低请按 FAQ 修改。

首次运行将自动下载配置中的 [internlm2-chat-7b](https://huggingface.co/internlm/internlm2-chat-7b)，请保证网络畅通。

- **非 docker 用户**。如果你**不**使用 docker 环境，可以一次启动所有服务。

  ```shell
  # standalone
  python3 -m huixiangdou.main --standalone
  ..
  ErrorCode.SUCCESS,
  Query: 请教下视频流检测 跳帧  造成框一闪一闪的  有好的优化办法吗
  Reply:
  1. 帧率控制和跳帧策略是优化视频流检测性能的关键，但需要注意跳帧对检测结果的影响。
  2. 多线程处理和缓存机制可以提高检测效率，但需要注意检测结果的稳定性。
  3. 使用滑动窗口的方式可以减少跳帧和缓存对检测结果的影响。
  ```

- **docker 用户**。如果你正在使用 docker，`HuixiangDou` 的 Hybrid LLM Service 需要分离部署。

  ```shell
  # 首先启动 LLM 服务，监听 8888 端口
  python3 -m huixiangdou.service.llm_server_hybrid
  ..
  ======== Running on http://0.0.0.0:8888 ========
  (Press CTRL+C to quit)
  ```

  然后运行新容器，把宿主机的 IP (注意不是 docker 容器内的 IP) 配置进 `config.ini`，运行

  ```shell
  # config.ini
  [llm]
  ..
  client_url = "http://10.140.24.142:9999/inference" # 举例，这里需要你换成宿主机 IP

  # 执行 main
  python3 -m huixiangdou.main
  ..
  ErrorCode.SUCCESS,
  Query: 请教下视频流检测..
  ```

## STEP3.集成到飞书\[可选\]

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
python3 -m huixiangdou.main --standalone # 非 docker 用户
python3 -m huixiangdou.main # docker 用户
```

<img src="./resource/figures/lark-example.png" width="400">

如果还需要从飞书群读取群聊消息，见[飞书开发者广场-添加应用能力-机器人](https://open.feishu.cn/app?lang=zh-CN)。

## STEP4.高级版\[可选\]

基础版可能效果不佳，可开启以下特性来提升效果。配置模板请参照 [config-advanced.ini](./config-advanced.ini)

1. 使用更高精度 local LLM

   把 config.ini 中的`llm.local` 模型调整为 `internlm2-20B`。
   此选项效果显著，但需要更大的 GPU 显存。

2. Hybrid LLM Service

   对于支持 [openai](https://pypi.org/project/openai/) 接口的 LLM 服务，茴香豆可以发挥它的 Long Context 能力。
   以 [kimi](https://platform.moonshot.cn/) 为例，以下是 `config.ini` 配置示例：

   ```shell
   # config.ini
   [llm]
   enable_local = 1
   enable_remote = 1
   ..
   [llm.server]
   ..
   # open https://platform.moonshot.cn/
   remote_type = "kimi"
   remote_api_key = "YOUR-KIMI-API-KEY"
   remote_llm_max_text_length = 128000
   remote_llm_model = "moonshot-v1-128k"
   ```

   我们同样支持 chatgpt API。注意此特性会增加响应耗时和运行成本。

3. repo 搜索增强

   此特性适合处理疑难问题，需要基础开发能力调整 prompt。

   - 点击 [sourcegraph-account-access](https://sourcegraph.com/users/tpoisonooo/settings/tokens) 获取 token

     ```shell
     # open https://github.com/sourcegraph/src-cli#installation
     sudo curl -L https://sourcegraph.com/.api/src-cli/src_linux_amd64 -o /usr/local/bin/src && chmod +x /usr/local/bin/src

     # 开启 sg 搜索，并且把 token 填入 config.ini
     [worker]
     enable_sg_search = 1 # first enable sg search
     ..
     [sg_search]
     ..
     src_access_token = "${YOUR_ACCESS_TOKEN}"
     ```

   - 编辑 repo 的名字和简介，我们以 opencompass 为例

     ```shell
     # config.ini
     # add your repo here, we just take opencompass and lmdeploy as example
     [sg_search.opencompass]
     github_repo_id = "open-compass/opencompass"
     introduction = "用于评测大型语言模型（LLM）.."
     ```

   - 使用 `python3 -m huixiangdou.service.sg_search` 单测，返回内容应包含 opencompass 源码和文档

     ```shell
     python3 -m huixiangdou.service.sg_search
     ..
     "filepath": "opencompass/datasets/longbench/longbench_trivia_qa.py",
     "content": "from datasets import Dataset..
     ```

   运行 `main.py`，茴香豆将在合适的时机，启用搜索增强。

4. 调参

   针对业务场景调参往往不可避免。

   - 参照 [data.json](./tests/data.json) 增加真实数据，运行 [test_intention_prompt.py](./tests/test_intention_prompt.py) 得到合适的 prompt 和阈值，更新进 [worker](./huixiangdou/service/worker.py)
   - 根据模型支持的最大长度，调整[搜索结果个数](./huixiangdou/service/worker.py)
   - 按照场景偏好，修改 config.ini 中的 `web_search.domain_partial_order`，即搜索结果偏序

# 🛠️ FAQ

1. 如何接入其他 IM ？

   - 企业微信。请查看[企业微信应用开发指南](https://developer.work.weixin.qq.com/document/path/90594)
   - 个人微信。我们已向微信团队确认暂无 API，[itchat](https://github.com/littlecodersh/ItChat) 或许有帮助（**注意风险**）
   - 钉钉。参考[钉钉开放平台-自定义机器人接入](https://open.dingtalk.com/document/robots/custom-robot-access)

2. 机器人太高冷/太嘴碎怎么办？

   - 把真实场景中，应该回答的问题填入`resource/good_questions.json`，应该拒绝的填入`resource/bad_questions.json`
   - 调整 `repodir` 中的文档，确保不包含场景无关内容

   重新执行 `feature_store` 来更新阈值和特征库

3. 启动正常，但运行期间显存 OOM 怎么办？

   基于 transformers 结构的 LLM 长文本需要更多显存，此时需要对模型做 kv cache 量化，如 [lmdeploy 量化说明](https://github.com/InternLM/lmdeploy/blob/main/docs/en/kv_int8.md)。然后使用 docker 独立部署 Hybrid LLM Service。

4. 如何接入其他 local LLM/ 接入后效果不理想怎么办？

   - 打开 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py)，增加新的 LLM 推理实现
   - 参照 [test_intention_prompt 和测试数据](./tests/test_intention_prompt.py)，针对新模型调整 prompt 和阈值，更新到 [worker.py](./huixiangdou/service/worker.py)

5. 响应太慢/网络请求总是失败怎么办？

   - 参考 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) 增加指数退避重传
   - local LLM 替换为 [lmdeploy](https://github.com/internlm/lmdeploy) 等推理框架，而非原生的 huggingface/transformers

6. 机器配置低，GPU 显存不足怎么办？

   此时无法运行 local LLM，只能用 remote LLM 配合 text2vec 执行 pipeline。请确保 `config.ini` 只使用 remote LLM，关闭 local LLM

# 📝 引用

```shell
@misc{2023HuixiangDou,
    title={HuixiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
    author={HuixiangDou Contributors},
    howpublished = {\url{https://github.com/internlm/huixiangdou}},
    year={2023}
}
```
