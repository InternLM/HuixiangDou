# 🎚️ 版本升级
[HuixiangDou2](https://github.com/tpoisonooo/HuixiangDou2) 是在植物领域验证有效的 GraphRAG 方案。如果你关注 **HuixiangDou 在非计算机领域的效果**，试试新版。

---

[English](README.md) | 简体中文

<div align="center">
<img src="resource/logo_black.svg" width="555px"/>

<div align="center">
  <a href="https://cdn.vansin.top/internlm/dou.jpg" target="_blank">
    <img alt="Wechat" src="https://img.shields.io/badge/wechat-robot%20inside-brightgreen?logo=wechat&logoColor=white" />
  </a>
  <a href="https://huixiangdou.readthedocs.io/zh-cn/latest/" target="_blank">
    <img alt="Readthedocs" src="https://img.shields.io/badge/readthedocs-chat%20with%20AI-brightgreen?logo=readthedocs&logoColor=white" />
  </a>
  <!-- <a href="https://huixiangdou.readthedocs.io/zh-cn/latest/" target="_blank">
    <img alt="Readthedocs" src="https://img.shields.io/badge/readthedocs-black?logo=readthedocs&logoColor=white" />
  </a> -->
  <a href="https://youtu.be/ylXrT-Tei-Y" target="_blank">
    <img alt="YouTube" src="https://img.shields.io/badge/YouTube-black?logo=youtube&logoColor=red" />
  </a>
  <a href="https://www.bilibili.com/video/BV1S2421N7mn" target="_blank">
    <img alt="BiliBili" src="https://img.shields.io/badge/BiliBili-pink?logo=bilibili&logoColor=white" />
  </a>
  <a href="https://discord.gg/TW4ZBpZZ" target="_blank">
    <img alt="discord" src="https://img.shields.io/badge/discord-red?logo=discord&logoColor=white" />
  </a>
  <a href="https://arxiv.org/abs/2401.08772" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-2401.08772%20-darkred?logo=arxiv&logoColor=white" />
  </a>
  <a href="https://arxiv.org/abs/2405.02817" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-2405.02817%20-darkred?logo=arxiv&logoColor=white" />
  </a>
</div>

</div>

HuixiangDou 是一个基于 LLM 的专业知识助手，优势：

1. 设计预处理、拒答、响应三阶段 pipeline：
    * `chat_in_group` 群聊场景，解答问题时不会消息泛滥。见 [2401.08772](https://arxiv.org/abs/2401.08772)，[2405.02817](https://arxiv.org/abs/2405.02817)，[混合检索](./docs/zh/doc_knowledge_graph.md)和[业务数据精度测试](./evaluation)
    * `chat_with_repo` 实时聊天场景，响应更快
2. 无需训练适用各行业，提供 CPU-only、2G、10G、20G、80G 规格配置
3. 提供一整套前后端 web、android、算法源码，工业级开源可商用

查看[茴香豆已运行在哪些场景](./huixiangdou-inside.md)，当前公共服务状况：
- [readthedocs ChatWithAI](https://huixiangdou.readthedocs.io/en/latest/) cpu-only 可用
- [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web) 使用 GPU，持续维护
- [微信群](https://cdn.vansin.top/internlm/dou.jpg) 有接入成本。所有代码已运行一年验证可用，请自行部署 [免费](https://github.com/InternLM/HuixiangDou/blob/main/docs/zh/doc_add_wechat_accessibility.md) 或 [商业](https://github.com/InternLM/HuixiangDou/blob/main/docs/zh/doc_add_wechat_commercial.md) 版
  
如果对你有用，麻烦 star 一下⭐

# 🔆 新功能

Web 版已发布到 [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web)，可以创建自己的知识库、更新正反例、开关网络搜索，聊天测试效果后，集成到飞书/微信群。

Web 版视频教程见 [BiliBili](https://www.bilibili.com/video/BV1S2421N7mn) 和 [YouTube](https://www.youtube.com/watch?v=ylXrT-Tei-Y)。

Web 版给 android 的接口，也支持非 android 调用，见[python 样例代码](./tests/test_openxlab_android_api.py)。

- \[2025/03\] [在多个微信群中转发消息](./docs/zh/doc_merge_wechat_group.md)
- \[2024/09\] [倒排索引](https://github.com/InternLM/HuixiangDou/pull/387)让 LLM 更偏向使用领域知识 🎯
- \[2024/09\] 稀疏方法实现[代码检索](./huixiangdou/service/parallel_pipeline.py)
- \[2024/08\] ["chat_with readthedocs"](https://huixiangdou.readthedocs.io/zh-cn/latest/) ，见[集成说明](./docs/zh/doc_add_readthedocs.md)
- \[2024/07\] 图文检索 & 移除 `langchain` 👍
- \[2024/07\] [混合知识图谱和稠密检索，F1 提升 1.7%](./docs/zh/doc_knowledge_graph.md) 🎯
- \[2024/06\] [评估 chunksize，splitter 和 text2vec 模型](./evaluation) 🎯
- \[2024/05\] [wkteam 微信接入](./docs/zh/doc_add_wechat_commercial.md)，整合图片&公众号解析、集成指代消歧
- \[2024/05\] [SFT LLM 处理 NLP 任务，F1 提升 29%](./sft/) 🎯
  <table>
      <tr>
          <td>🤗</td>
          <td><a href="https://huggingface.co/tpoisonooo/HuixiangDou-CR-LoRA-Qwen-14B">LoRA-Qwen1.5-14B</a></td>
          <td><a href="https://huggingface.co/tpoisonooo/HuixiangDou-CR-LoRA-Qwen-32B">LoRA-Qwen1.5-32B</a></td>
          <td><a href="https://huggingface.co/datasets/tpoisonooo/HuixiangDou-CR/tree/main">alpaca 数据</a></td>
          <td><a href="https://arxiv.org/abs/2405.02817">arXiv</a></td>
      </tr>
  </table>
- \[2024/04\] 实现 [RAG 标注 SFT 问答数据和样例](./docs/zh/doc_rag_annotate_sft_data.md)
- \[2024/04\] 发布 [web 前后端服务源码](./web) 👍
- \[2024/03\] 新的[个人微信集成方法](./docs/zh/doc_add_wechat_accessibility.md)和[**预编译 apk**](https://github.com/InternLM/HuixiangDou/releases/download/v0.1.0rc1/huixiangdou-20240508.apk) !
- \[2024/02\] \[实验功能\] [微信群](https://cdn.vansin.top/internlm/dou.jpg) 集成多模态以实现 OCR

# 📖 支持情况

<table align="center">
  <tbody>
    <tr align="center" valign="bottom">
      <td>
        <b>LLM</b>
      </td>
      <td>
        <b>文件格式</b>
      </td>
      <td>
        <b>检索方法</b>
      </td>
      <td>
        <b>接入方法</b>
      </td>
      <td>
        <b>预处理</b>
      </td>
    </tr>
    <tr valign="top">
      <td>

- [InternLM2/InternLM2.5](https://github.com/InternLM/InternLM)
- [Qwen/Qwen2](https://github.com/QwenLM/Qwen2)
- [浦语](https://internlm.openxlab.org.cn/)
- [StepFun](https://platform.stepfun.com)
- [KIMI](https://kimi.moonshot.cn)
- [DeepSeek](https://www.deepseek.com)
- [GLM (ZHIPU)](https://www.zhipuai.cn)
- [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud)
- [Xi-Api](https://api.xi-ai.cn)

</td>
<td>

- pdf
- word
- excel
- ppt
- html
- markdown
- txt

</td>

<td>

- 文档用稠密，代码用稀疏
- [知识图谱](./docs/zh/doc_knowledge_graph.md)
- [联网搜索](./huixiangdou/service/web_search.py)
- [SourceGraph](https://sourcegraph.com)
- 图文混合

</td>

<td>

- 微信（[android](./docs/zh/doc_add_wechat_accessibility.md)/[wkteam](./docs/zh/doc_add_wechat_commercial.md)）
- 飞书
- [OpenXLab Web](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web)
- [Gradio Demo](./huixiangdou/gradio_ui.py)
- [HTTP Server](./huixiangdou/server.py)
- [Read the Docs](./docs/zh/doc_add_readthedocs.md)

</td>

<td>

- [指代消歧](https://arxiv.org/abs/2405.02817)

</td>

</tr>
  </tbody>
</table>

# 📦 硬件要求

以下是不同特性所需显存，区别仅在**配置选项是否开启**。

|                     配置示例                     | 显存需求 |                                                                                 描述                                                                                 |                             Linux 系统已验证设备                              |
| :----------------------------------------------: | :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
|         [config-cpu.ini](./config-cpu.ini)         |   -    | 用 [siliconcloud](https://siliconflow.cn/) API <br/>仅检索文本 | ![](https://img.shields.io/badge/x86-passed-blue?style=for-the-badge) |
|         [config-2G.ini](./config-2G.ini)         |   2GB    | 用 openai API（如 [kimi](https://kimi.moonshot.cn)、[deepseek](https://platform.deepseek.com/usage) 和 [stepfun](https://platform.stepfun.com/)）<br/>仅检索文本 | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |
| [config-multimodal.ini](./config-multimodal.ini) |   10GB   |                                                                    用 openai API 做 LLM，图文检索                                                                    | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
|       【标准版】[config.ini](./config.ini)       |   19GB   |                                                                         本地部署 LLM，单模态                                                                         | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
|   [config-advanced.ini](./config-advanced.ini)   |   80GB   |                                                                本地 LLM，指代消歧，单模态，微信群实用                                                                | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |

# 🔥 运行标准版

我们以标准版（本地运行 LLM，纯文本检索）为例，介绍 HuixiangDou 功能。其他版本仅仅是配置选项不同。

## 一、下载模型，安装依赖

首先[点击同意 BCE 模型协议](https://huggingface.co/maidalun1020/bce-embedding-base_v1)，命令行登录 huggingface

```shell
huggingface-cli login
```

安装依赖

```bash
# parsing `word` format requirements
apt update
apt install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev
# python requirements
pip install -r requirements.txt
# python3.8 安装 faiss-gpu 而不是 faiss
```

## 二、创建知识库，执行测试

我们将用 mmpose 的文档构建 mmpose 知识库，过滤问题。如有自己的文档，放入 `repodir` 下即可。

复制下面所有命令（包含 '#' 符号）建立知识库。

```shell
# 下载知识库，我们仅以 mmpose 的文档为例。repodir下可以放任何自己的文档
cd HuixiangDou
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1 repodir/mmpose

# 把 repodir 的特征保存到 workdir，把正反例阈值更新进 `config.ini`
mkdir workdir
python3 -m huixiangdou.service.feature_store
```

结束后执行 `python3 -m huixiangdou.main --standalone`，此时回复 mmpose 相关问题（和知识库相关），同时不响应天气问题。

```bash
python3 -m huixiangdou.main --standalone

+-----------------------+---------+--------------------------------+-----------------+
|         Query         |  State  |         Reply                  |   References    |
+=======================+=========+================================+=================+
| 请问如何安装 mmpose ?   | success | 要安装 mmpose，请按照以下步骤操作..| installation.md |
--------------------------------------------------------------------------------------
| 今天天气如何？          | unrelated| ..                            |                 |
+-----------------------+---------+--------------------------------+-----------------+
🔆 Input your question here, type `bye` for exit:
..
```

> \[!NOTE\]
>
> <div align="center">
> 如果每次重启 LLM 太慢，先 <b>python3 -m huixiangdou.service.llm_server_hybrid</b>；然后开新窗口，每次只执行 <b>python3 -m huixiangdou.main</b> 不重启 LLM。
> </div>

<br/>

💡 也可以启动 `gradio` 搭建一个简易的 Web UI，默认绑定 7860 端口：

```bash
python3 -m huixiangdou.gradio_ui
# 若已单独运行 `llm_server_hybrid.py`，可以 
# python3 -m huixiangdou.gradio_ui --no-standalone
```

<video src="https://github.com/user-attachments/assets/9e5dbb30-1dc1-42ad-a7d4-dc7380676554" ></video>

或者启动服务端，监听 23333 端口。默认使用 `chat_with_repo` pipeline：
```bash
python3 -m huixiangdou.server

# cURL 测试状态回调接口
curl -X POST http://127.0.0.1:23333/huixiangdou_stream  -H "Content-Type: application/json" -d '{"text": "how to install mmpose","image": ""}'
# cURL 测试同步接口
curl -X POST http://127.0.0.1:23333/huixiangdou_inference  -H "Content-Type: application/json" -d '{"text": "how to install mmpose","image": ""}'
```

请调整 `repodir` 文档、[good_questions](./resource/good_questions.json) 和 [bad_questions](./resource/bad_questions.json)，尝试自己的领域知识（医疗，金融，电力等）。

## 三、集成到飞书、微信群

- [**单向**发送到飞书群](./docs/zh/doc_send_only_lark_group.md)
- [**双向**飞书群收发、撤回](./docs/zh/doc_add_lark_group.md)
- [个微 android 接入](./docs/zh/doc_add_wechat_accessibility.md)
- [个微 wkteam 接入](./docs/zh/doc_add_wechat_commercial.md)

## 四、WEB 前后端部署，零编程集成飞书微信

我们提供了完整的 typescript 前端和 python 后端服务源码：

- 支持多租户管理
- 零编程接入飞书、微信群
- 架构松散，适合 k8s

效果同 [OpenXlab APP](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web) ，请阅读 [web 部署文档](./web/README.md)。

# 🍴 其他配置

## **纯 CPU 版**

若没有 GPU，可以使用 [siliconcloud](https://siliconflow.cn/) API 完成模型推理。

以 docker miniconda+Python3.11 为例，安装 cpu 依赖，运行：

```bash
# 启动容器
docker run  -v /path/to/huixiangdou:/huixiangdou  -p 7860:7860 -p 23333:23333  -it continuumio/miniconda3 /bin/bash
# 装依赖
apt update
apt install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev
python3 -m pip install -r requirements-cpu.txt
# 建立知识库
python3 -m huixiangdou.service.feature_store  --config_path config-cpu.ini
# 问答测试
python3 -m huixiangdou.main --standalone --config_path config-cpu.ini
# gradio UI
python3 -m huixiangdou.gradio_ui --config_path config-cpu.ini
```

如果装依赖太慢，[dockerhub 里](https://hub.docker.com/repository/docker/tpoisonooo/huixiangdou/tags)提供了安装好依赖的镜像，docker 启动时替换即可。

## **2G 实惠版**

如果你的显存超过 1.8G，或追求性价比。此配置扔掉了本地 LLM，使用 remote LLM 代替，其他和标准版相同。

以 siliconcloud 为例，把[官网申请](https://siliconflow.cn/zh-cn/siliconcloud) 的 API TOKEN 填入 `config-2G.ini`

```toml
[llm]
enable_local = 0   # 关掉本地 LLM
enable_remote = 1  # 只用远程
..
remote_type = "siliconcloud"   # 选择 siliconcloud
remote_api_key = "YOUR-API-KEY-HERE" # 填 API key
remote_llm_model = "alibaba/Qwen1.5-110B-Chat"
```

> \[!NOTE\]
>
> <div align="center">
> 每次问答最坏情况要调用 7 次 LLM，受免费用户 RPM 限制，可修改 config.ini 中 <b>rpm</b> 参数
> </div>

执行命令获取问答结果

```shell
python3 -m huixiangdou.main --standalone --config-path config-2G.ini # 一次启动所有服务
```

## **10G 多模态版**

如果你有 10G 显存，那么可以进一步支持图文检索。仅需修改 config.ini 使用的模型。

```toml
# config-multimodal.ini
# !!! Download `https://huggingface.co/BAAI/bge-visualized/blob/main/Visualized_m3.pth` to `bge-m3` folder !!!
embedding_model_path = "BAAI/bge-m3"
reranker_model_path = "BAAI/bge-reranker-v2-minicpm-layerwise"
```

需要注意：

- 先下载 [bge-m3](https://huggingface.co/BAAI/bge-m3)，然后把 [Visualized_m3.pth](https://huggingface.co/BAAI/bge-visualized/blob/main/Visualized_m3.pth) 放进 `bge-m3` 目录
- FlagEmbedding 需要安装 master 最新版，我们做了 [bugfix](https://github.com/FlagOpen/FlagEmbedding/commit/3f84da0796d5badc3ad519870612f1f18ff0d1d3)；[这里](https://github.com/FlagOpen/FlagEmbedding/blob/master/FlagEmbedding/visual/eva_clip/bpe_simple_vocab_16e6.txt.gz)可以下载 BGE 打包漏掉的 `bpe_simple_vocab_16e6.txt.gz`
- 安装 [requirements/multimodal.txt](./requirements/multimodal.txt)

运行 gradio 测试，图文检索效果见[这里](https://github.com/InternLM/HuixiangDou/pull/326).

```bash
python3 tests/test_query_gradio.py
```

## **80G 完整版**

微信体验群里的 “茴香豆” 开启了全部功能：

- Serper 搜索及 SourceGraph 搜索增强
- 群聊图片、微信公众号解析
- 文本指代消歧
- 混合 LLM
- 知识库为 openmmlab 相关的 12 个 repo（1700 个文档），拒绝闲聊

请阅读以下话题：

- [混合**知识图谱**和稠密检索提升精度](./docs/zh/doc_knowledge_graph.md)
- [参照 config-advanced.ini 配置提升效果](./docs/zh/doc_full_dev.md)
- [群聊场景指代消歧训练](./sft)
- [使用 wkteam 微信接入，整合图片、公众号解析和指代消歧](./docs/zh/doc_add_wechat_commercial.md)
- [使用 rag.py 标注 SFT 训练数据](./docs/zh/doc_rag_annotate_sft_data.md)

## **移动端**

贡献者提供了[android工具](./android) 完成微信接入。方案基于系统层 API，原理上可以控制任何 UI（不限于通讯软件）。

# 🛠️ FAQ

1. 对于通用问题（如 “番茄是什么” ），我希望 LLM 优先用领域知识（如 “普罗旺斯番茄”）怎么办？

    参照 [PR](https://github.com/InternLM/HuixiangDou/pull/387)，准备实体列表，构建特征库时传入列表，`ParallelPipeline`检索会基于倒排索引增大召回

2. 机器人太高冷/太嘴碎怎么办？

   - 把真实场景中，应该回答的问题填入`resource/good_questions.json`，应该拒绝的填入`resource/bad_questions.json`
   - 调整 `repodir` 中的文档，确保不包含场景无关内容

   重新执行 `feature_store` 来更新阈值和特征库。

   ⚠️ 如果你足够自信，也可以直接修改 config.ini 的 `reject_throttle` 数值，一般来说 0.5 是很高的值；0.2 过低。

3. 启动正常，但运行期间显存 OOM 怎么办？

   基于 transformers 结构的 LLM 长文本需要更多显存，此时需要对模型做 kv cache 量化，如 [lmdeploy 量化说明](https://github.com/InternLM/lmdeploy/blob/main/docs/zh_cn/quantization)。然后使用 docker 独立部署 Hybrid LLM Service。

4. 如何接入其他 local LLM / 接入后效果不理想怎么办？

   - 打开 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py)，增加新的 LLM 推理实现
   - 参照 [test_intention_prompt 和测试数据](./tests/test_intention_prompt.py)，针对新模型调整 prompt 和阈值，更新到 [prompt.py](./huixiangdou/service/prompt.py)

5. 响应太慢/网络请求总是失败怎么办？

   - 参考 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) 增加指数退避重传
   - local LLM 替换为 [lmdeploy](https://github.com/internlm/lmdeploy) 等推理框架，而非原生的 huggingface/transformers

6. 机器配置低，GPU 显存不足怎么办？

   此时无法运行 local LLM，只能用 remote LLM 配合 text2vec 执行 pipeline。请确保 `config.ini` 只使用 remote LLM，关闭 local LLM

7. 报错 `(500, 'Internal Server Error')`，意为 standalone 模式启动的 LLM 服务没访问到。按如下方式定位

   - 执行 `python3 -m huixiangdou.service.llm_server_hybrid` 确定 LLM 服务无报错，监听的端口和配置一致。检查结束后按 ctrl-c 关掉。
   - 检查 `config.ini` 中各种 TOKEN 书写正确。

# 🍀 致谢

- [KIMI](https://kimi.moonshot.cn/): 长文本 LLM，支持直接上传文件
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding): BAAI RAG 组
- [BCEmbedding](https://github.com/netease-youdao/BCEmbedding): 中英双语特征模型
- [Langchain-ChatChat](https://github.com/chatchat-space/Langchain-Chatchat): Langchain 和 ChatGLM 的应用
- [GrabRedEnvelope](https://github.com/xbdcc/GrabRedEnvelope): 微信抢红包

# 📝 引用

```shell
@misc{kong2024huixiangdou,
      title={HuiXiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
      author={Huanjun Kong and Songyang Zhang and Jiaying Li and Min Xiao and Jun Xu and Kai Chen},
      year={2024},
      eprint={2401.08772},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}

@misc{kong2024labelingsupervisedfinetuningdata,
      title={Labeling supervised fine-tuning data with the scaling law}, 
      author={Huanjun Kong},
      year={2024},
      eprint={2405.02817},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2405.02817}, 
}

@misc{kong2025huixiangdou2robustlyoptimizedgraphrag,
      title={HuixiangDou2: A Robustly Optimized GraphRAG Approach}, 
      author={Huanjun Kong and Zhefan Wang and Chenyang Wang and Zhe Ma and Nanqing Dong},
      year={2025},
      eprint={2503.06474},
      archivePrefix={arXiv},
      primaryClass={cs.IR},
      url={https://arxiv.org/abs/2503.06474}, 
}
```
