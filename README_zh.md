[English](README.md) | 简体中文

<div align="center">

<img src="resource/logo_black.svg" width="500px"/>

<div align="center">
  <a href="resource/figures/wechat.jpg" target="_blank">
    <img alt="Wechat" src="https://img.shields.io/badge/wechat-assistant%20inside-brightgreen?logo=wechat&logoColor=white" />
  </a>
  <a href="https://arxiv.org/abs/2401.08772" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-paper%20-darkred?logo=arxiv&logoColor=white" />
  </a>
  <a href="https://pypi.org/project/huixiangdou/" target="_blank">
    <img alt="PyPI" src="https://img.shields.io/badge/PyPI-install-blue?logo=pypi&logoColor=white" />
  </a>
  <a href="https://youtu.be/ylXrT-Tei-Y" target="_blank">
    <img alt="YouTube" src="https://img.shields.io/badge/YouTube-black?logo=youtube&logoColor=red" />
  </a>
  <a href="https://www.bilibili.com/video/BV1S2421N7mn" target="_blank">
    <img alt="BiliBili" src="https://img.shields.io/badge/BiliBili-pink?logo=bilibili&logoColor=white" />
  </a>
</div>

</div>

“茴香豆”是一个基于 LLM 的领域知识助手。特点：

1. 应对群聊这类复杂场景，解答用户问题的同时，不会消息泛滥
2. 提出一套解答技术问题的算法 pipeline
3. 部署成本低，只需要 LLM 模型满足 4 个 trait 即可解答大部分用户问题，见[技术报告 arxiv2401.08772](https://arxiv.org/abs/2401.08772)

查看[茴香豆已运行在哪些场景](./huixiangdou-inside.md)；加入[微信群](resource/figures/wechat.jpg)直接体验群聊助手效果。

如果对你有用，麻烦 star 一下⭐

# 🔆 新功能

茴香豆 Web 版已发布到 [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web)，可以创建自己的知识库、更新正反例、开关网络搜索，聊天测试效果后，集成到飞书/微信群。

Web 版视频教程见 [BiliBili](https://www.bilibili.com/video/BV1S2421N7mn) 和 [YouTube](https://www.youtube.com/watch?v=ylXrT-Tei-Y)。

- \[2024/03\] 支持 `ppt` 和 `html` 格式
- \[2024/03\] 优化 `pdf` 和表格解析，改善精度并加速
- \[2024/03\] 支持 [zhipuai](https://zhipuai.cn) 和 [xi-api 国内 gpt 代理](https://api.xi-ai.cn)，见 `config.ini`
- \[2024/03\] 新的[个人微信集成方法](./docs/add_wechat_accessibility_zh.md)和[**预编译 apk**](https://github.com/InternLM/HuixiangDou/releases/download/v0.1.0rc1/huixiangdou-1.0.0.apk) !
- \[2024/03\] 支持 `pdf`/`word`/`excel`，返回引用的文件名或 Web URL
- \[2024/02\] 用 [BCEmbedding](https://github.com/netease-youdao/BCEmbedding) rerank 提升检索精度 👍
- \[2024/02\] [支持 deepseek](https://github.com/InternLM/HuixiangDou/blob/main/README_zh.md#step2-%E8%BF%90%E8%A1%8C%E5%9F%BA%E7%A1%80%E7%89%88%E6%8A%80%E6%9C%AF%E5%8A%A9%E6%89%8B) 和 qwen1.5; 按 GPU 显存动态选模型
- \[2024/02\] \[实验功能\] [微信群](https://github.com/InternLM/HuixiangDou/blob/main/resource/figures/wechat.jpg) 集成多模态以实现 OCR
- \[2024/01\] 实现[个人微信接入](./docs/add_wechat_group_zh.md); [飞书群收发和撤回](./docs/add_lark_group_zh.md)

# 📦 硬件要求

以下是运行茴香豆的硬件需求。建议遵循部署流程，从基础版开始，逐渐体验高级特性。

|  版本  | GPU显存需求 |                                                                                          描述                                                                                          |                             Linux 系统已验证设备                              |
| :----: | :---------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
| 体验版 |    1.5GB    | 用 [openai API](https://pypi.org/project/openai/)（如 [kimi](https://kimi.moonshot.cn) 和 [deepseek](https://platform.deepseek.com/usage)）替代本地 LLM，处理源码级问题。<br/>限额免费 | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |
| 基础版 |    19GB     |                                                                         本地部署 LLM，能回答领域知识的基础问题                                                                         | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
| 高级版 |    40GB     |                                                                      充分利用检索+长文本能力，能够回答源码级问题                                                                       | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |

如果你只有 2G 显存，或追求性价比💰，[看这个知乎文档](https://zhuanlan.zhihu.com/p/685205206)。

# 🔥 运行

我们将以 mmpose 和一些 `word`/`excel`/`pdf`/`ppt` 测试文档为例，介绍如何把知识助手部署到飞书群

## STEP1. 建立话题特征库

由于 [embedding](https://huggingface.co/maidalun1020/bce-embedding-base_v1) 和 [rerank](https://huggingface.co/maidalun1020/bce-reranker-base_v1) 模型需要验证才能获取，你需要登录 huggingface。为了加速下载你可以使用 [hf 国内镜像](https://hf-mirror.com/)。

```shell
huggingface-cli login
```

复制下面所有命令（包含 '#' 符号）执行。

```shell
# 下载 repo
git clone https://github.com/internlm/huixiangdou --depth=1 && cd huixiangdou

# 下载聊天话题
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1 repodir/mmpose
git clone https://github.com/tpoisonooo/huixiangdou-testdata --depth=1 repodir/testdata

# 安装解析 word 文档所需依赖
apt install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev
# 安装 python 依赖
pip install -r requirements.txt

# 把 repodir 的特征保存到 workdir
mkdir workdir
python3 -m huixiangdou.service.feature_store
```

首次运行将自动下载配置中的 [text2vec 模型](./config.ini)。考虑到 huggingface 连接问题，建议先手动下载到本地，然后在 `config.ini` 设置模型路径。例如：

```shell
# config.ini
[feature_store]
..
model_path = "/path/to/text2vec-model"

# .github/scripts/config-ci.ini 是一个修改好的示例，用于本项目的 CI
```

运行结束后，茴香豆能够区分应该处理哪些用户话题，哪些闲聊应该拒绝。请编辑 [good_questions](./resource/good_questions.json) 和 [bad_questions](./resource/bad_questions.json)，尝试自己的领域知识（医疗，金融，电力等）。

```shell
The optimal threshold is: 0.5447442409012104, saved it..
# 拒绝闲聊
reject query: 有啥中文的 text to speech 模型吗?
reject query: 今天中午吃什么
# 接受底库话题
process query: mmpose 如何安装？
process query: 使用科研仪器需要注意什么？
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

\[仅体验版需要这步\] 如果你的机器显存不足以本地运行 7B LLM（低于 15G），可开启 `kimi` 或 `deepseek` [白嫖 3kw 限免 token](https://platform.deepseek.com/)。参照 [config-experience.ini](./config-experience.ini)

```ini
# config.ini
[llm]
enable_local = 0
enable_remote = 1
..
[llm.server]
..
remote_type = "deepseek"
remote_api_key = "YOUR-API-KEY"
remote_llm_max_text_length = 16000
remote_llm_model = "deepseek-chat"
```

默认配置中 `enable_local=1`，首次运行将根据显存大小，自动下载不同的 LLM，请保证网络畅通。建议先手动下载到本地，再修改 `config.ini` 中模型路径。

- **非 docker 用户**。如果你**不**使用 docker 环境，可以一次启动所有服务。

  ```shell
  # standalone
  python3 -m huixiangdou.main --standalone
  ..
  ErrorCode.SUCCESS,
  Query: 请问如何安装 mmpose ?
  Reply:
  要安装 mmpose，请按照以下步骤操作：
  1. **准备环境**：
  - 安装 Miniconda。
  - 创建并激活一个名为 openmmlab 的 conda 环境。
  ..
  ```

  注：如果使用 deepseek 进行 remote llm 调用，出现 400 错误可能是因为安全审查；在 [huixiangdou/main.py](huixiangdou/main.py) 中修改 `queries = ['请问如何安装 mmpose ?']` 为其他问题即可正常运行。

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
  Query: 请问如何安装 mmpose..
  ```

## STEP3.集成飞书/个人微信\[可选\]

点击[创建飞书自定义机器人](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)，获取回调 WEBHOOK_URL，填写到 config.ini

```ini
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

- [运行完整的飞书群组收发、撤回功能](./docs/add_lark_group_zh.md)
- [个人微信接入示例](./docs/add_wechat_group_zh.md)
- 还可以参考[钉钉开放平台-自定义机器人接入](https://open.dingtalk.com/document/robots/custom-robot-access)

## STEP4.高级版\[可选\]

基础版可能效果不佳，可开启以下特性来提升效果。配置模板请参照 [config-advanced.ini](./config-advanced.ini)

1. 使用更高精度 local LLM

   把 config.ini 中的`llm.local` 模型调整为 `internlm2-chat-20b`。
   此选项效果显著，但需要更大的 GPU 显存。

2. Hybrid LLM Service

   对于支持 [openai](https://pypi.org/project/openai/) 接口的 LLM 服务，茴香豆可以发挥它的 Long Context 能力。
   以 [kimi](https://platform.moonshot.cn/) 为例，以下是 `config.ini` 配置示例：

   ```ini
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

     ```ini
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

1. 机器人太高冷/太嘴碎怎么办？

   - 把真实场景中，应该回答的问题填入`resource/good_questions.json`，应该拒绝的填入`resource/bad_questions.json`
   - 调整 `repodir` 中的文档，确保不包含场景无关内容

   重新执行 `feature_store` 来更新阈值和特征库

2. 启动正常，但运行期间显存 OOM 怎么办？

   基于 transformers 结构的 LLM 长文本需要更多显存，此时需要对模型做 kv cache 量化，如 [lmdeploy 量化说明](https://github.com/InternLM/lmdeploy/blob/main/docs/zh_cn/quantization/kv_int8.md)。然后使用 docker 独立部署 Hybrid LLM Service。

3. 如何接入其他 local LLM / 接入后效果不理想怎么办？

   - 打开 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py)，增加新的 LLM 推理实现
   - 参照 [test_intention_prompt 和测试数据](./tests/test_intention_prompt.py)，针对新模型调整 prompt 和阈值，更新到 [worker.py](./huixiangdou/service/worker.py)

4. 响应太慢/网络请求总是失败怎么办？

   - 参考 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) 增加指数退避重传
   - local LLM 替换为 [lmdeploy](https://github.com/internlm/lmdeploy) 等推理框架，而非原生的 huggingface/transformers

5. 机器配置低，GPU 显存不足怎么办？

   此时无法运行 local LLM，只能用 remote LLM 配合 text2vec 执行 pipeline。请确保 `config.ini` 只使用 remote LLM，关闭 local LLM

# 🍀 致谢

- [kimi-chat](https://kimi.moonshot.cn/): 长文本 LLM，支持直接上传文件
- [BCEmbedding](https://github.com/netease-youdao/BCEmbedding): 中英双语特征模型
- [Langchain-ChatChat](https://github.com/chatchat-space/Langchain-Chatchat): Langchain 和 ChatGLM 的应用
- [GrabRedEnvelope](https://github.com/xbdcc/GrabRedEnvelope): 微信抢红包

# 📝 引用

```shell
@misc{kong2024huixiangdou,
      title={HuixiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
      author={Huanjun Kong and Songyang Zhang and Kai Chen},
      year={2024},
      eprint={2401.08772},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```
