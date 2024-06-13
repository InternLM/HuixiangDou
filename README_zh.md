[English](README.md) | 简体中文

<div align="center">

<img src="resource/logo_black.svg" width="555px"/>

<div align="center">
  <a href="resource/figures/wechat.jpg" target="_blank">
    <img alt="Wechat" src="https://img.shields.io/badge/wechat-robot%20inside-brightgreen?logo=wechat&logoColor=white" />
  </a>
  <a href="https://pypi.org/project/huixiangdou" target="_blank">
    <img alt="PyPI" src="https://img.shields.io/badge/PyPI-install-blue?logo=pypi&logoColor=white" />
  </a>
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
</div>

</div>

茴香豆是一个基于 LLM 的**群聊**知识助手，优势：

1. 设计预处理、拒答、响应三阶段 pipeline 应对群聊场景，解答问题同时不会消息泛滥。精髓见论文 [2401.08772](https://arxiv.org/abs/2401.08772) 和 [2405.02817](https://arxiv.org/abs/2405.02817)
2. 成本低至 1.5G 显存，无需训练适用各行业
3. 提供一整套前后端 web、android、算法源码，工业级开源可商用

查看[茴香豆已运行在哪些场景](./huixiangdou-inside.md)；加入[微信群](resource/figures/wechat.jpg)直接体验群聊助手效果。

如果对你有用，麻烦 star 一下⭐

# 🔆 新功能

茴香豆 Web 版已发布到 [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web)，可以创建自己的知识库、更新正反例、开关网络搜索，聊天测试效果后，集成到飞书/微信群。

Web 版视频教程见 [BiliBili](https://www.bilibili.com/video/BV1S2421N7mn) 和 [YouTube](https://www.youtube.com/watch?v=ylXrT-Tei-Y)。

- \[2024/05\] [wkteam 微信接入](./docs/add_wechat_commercial_zh.md)，整合图片&公众号解析、集成指代消歧
- \[2024/05\] [指代消歧微调](./sft/)
  <table>
      <tr>
          <td>🤗</td>
          <td><a href="https://huggingface.co/tpoisonooo/HuixiangDou-CR-LoRA-Qwen-14B">LoRA-Qwen1.5-14B</a></td>
          <td><a href="https://huggingface.co/tpoisonooo/HuixiangDou-CR-LoRA-Qwen-32B">LoRA-Qwen1.5-32B</a></td>
          <td><a href="https://huggingface.co/datasets/tpoisonooo/HuixiangDou-CR/tree/main">alpaca 数据</a></td>
          <td><a href="https://arxiv.org/abs/2405.02817">论文</a></td>
      </tr>
  </table>
- \[2024/04\] 实现 [RAG 标注 SFT 问答数据和样例](./docs/rag_annotate_sft_data_zh.md)
- \[2024/04\] 更新 [技术报告](./resource/HuixiangDou.pdf)
- \[2024/04\] 发布 [web 前后端服务源码](./web) 👍
- \[2024/03\] 新的[个人微信集成方法](./docs/add_wechat_accessibility_zh.md)和[**预编译 apk**](https://github.com/InternLM/HuixiangDou/releases/download/v0.1.0rc1/huixiangdou-1.0.0.apk) !
- \[2024/02\] \[实验功能\] [微信群](https://github.com/InternLM/HuixiangDou/blob/main/resource/figures/wechat.jpg) 集成多模态以实现 OCR

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
        <b>即时通讯软件</b>
      </td>
    </tr>
    <tr valign="top">
      <td>

- [InternLM2](https://github.com/InternLM/InternLM)
- [Qwen/Qwen2](https://github.com/QwenLM/Qwen2)
- [KIMI](https://kimi.moonshot.cn)
- [DeepSeek](https://www.deepseek.com)
- [Step](https://platform.stepfun.com)
- [GLM (ZHIPU)](https://www.zhipuai.cn)
- [SiliconCloud](https://siliconflow.cn/zh-cn/siliconcloud)
- [Xi-Api](https://api.xi-ai.cn)
- [OpenAOE](https://github.com/InternLM/OpenAOE)

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

- WeChat
- Lark
- ..

</td>

</tr>
  </tbody>
</table>

# 📦 硬件要求

以下是运行茴香豆的硬件需求。建议遵循部署流程，从标准版开始，逐渐体验复杂特性。

|  版本  | GPU显存需求 |                                                                                          描述                                                                                          |                             Linux 系统已验证设备                              |
| :----: | :---------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
| 实惠版 |    1.5GB    | 用 [openai API](https://pypi.org/project/openai/)（如 [kimi](https://kimi.moonshot.cn) 和 [deepseek](https://platform.deepseek.com/usage)）替代本地 LLM，处理源码级问题。<br/>限额免费 | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |
| 标准版 |    19GB     |                                                                         本地部署 LLM，能回答领域知识的基础问题                                                                         | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
| 完整版 |    40GB     |                                                                      充分利用检索+长文本能力，能够回答源码级问题                                                                       | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |

# 🔥 运行

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

茴香豆是基于 `config.ini` 配置实现的，按机器显存可以分成标准版（19G）、实惠版（1.5G）和完整版（40G）。

## 一、标准版

标准版会在本地运行 text2vec、rerank 和 7B 模型。

**STEP1.** 先不使用拒答流，直接运行一些测试用例：

```shell
# standalone 模式
# main 创建子进程运行 LLM API，然后向子进程发请求
python3 -m huixiangdou.main --standalone
..
Topics unrelated to the knowledge base.. 请问如何安装 mmpose ?, , []
..
Topics unrelated to the knowledge base.. 请问明天天气如何？, , []
```

> \[!NOTE\]
>
> <div align="center">
> 如果 huggingface 下载太慢，可以用国内镜像 <a href="https://hf-mirror.com">hf-mirror</a> 下载到本地。然后修改 <b>config.ini</b> 配置中模型的路径
> </div>

可以看到 `main.py` 示例问题处理结果相同，无论问深度学习相关的 mmpose 还是 `今天天气如何`。

**STEP2.** 用 mmpose 的文档构建 mmpose 知识库，开启拒答流。如有自己的文档，放入 `repodir` 下即可。

复制下面所有命令（包含 '#' 符号）执行。

```shell
# 下载知识库文档
cd HuixiangDou
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1 repodir/mmpose
git clone https://github.com/tpoisonooo/huixiangdou-testdata --depth=1 repodir/testdata

# 把 repodir 的特征保存到 workdir，把正反例阈值更新进 `config.ini`
mkdir workdir
python3 -m huixiangdou.service.feature_store
```

运行结束后再次测试 main
，茴香豆能够回答 mmpose 问题，同时拒答天气问题。

```bash
python3 -m huixiangdou.main --standalone
..success, 请问如何安装 mmpose ?, 要安装 mmpose，请按照以下步骤进行..
..Topics unrelated to the knowledge base..请问明天天气如何？
```

> \[!NOTE\]
>
> <div align="center">
> 如果每次重启 LLM 太慢，先 <b>python3 -m huixiangdou.service.llm_server_hybrid</b>；然后开新窗口，每次只执行 <b>python3 -m huixiangdou.main</b> 不重启 LLM。
> </div>

请调整 `repodir` 文档、[good_questions](./resource/good_questions.json) 和 [bad_questions](./resource/bad_questions.json)，尝试自己的领域知识（医疗，金融，电力等）。

**STEP3.** 测试发消息给飞书群\[可选\]

这一步主要是验证算法 pipeline 可靠，**STEP4** 同样支持即时通讯软件。

点击[创建飞书自定义机器人](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)，获取回调 WEBHOOK_URL，填写到 config.ini

```ini
# config.ini
..
[frontend]
type = "lark"
webhook_url = "${YOUR-LARK-WEBHOOK-URL}"
```

运行。结束后，技术助手的答复将**单向**发送到飞书群。

```shell
python3 -m huixiangdou.main --standalone # 非 docker 用户
python3 -m huixiangdou.main # docker 用户
```

<img src="./resource/figures/lark-example.png" width="400">

- [算法 pipeline 集成飞书群收发、撤回功能](./docs/add_lark_group_zh.md)
- [算法 pipeline 个微 android 接入](./docs/add_wechat_accessibility_zh.md)
- [算法 pipeline 个微 wkteam 接入](./docs/add_wechat_commercial_zh.md)

**STEP4.** WEB 前后端

我们提供了完整的前端 UI 和后端服务，支持：

- 多租户管理
- 零编程接入飞书、微信群

效果见 [OpenXlab APP](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web) ，请阅读[web部署文档](./web/README.md)。

## 二、实惠版

如果你的机器显存只有 2G，或追求性价比，只需要看[这个知乎文档](https://zhuanlan.zhihu.com/p/685205206)。

实惠版仅扔掉了本地 LLM，使用 remote LLM 代替，其他功能和标准版相同。

以 kimi 为例，把[官网申请](https://platform.moonshot.cn/) 的 API TOKEN 填入 `config-2G.ini`

```bash
# config-2G.ini
[llm]
enable_local = 0
enable_remote = 1
..
remote_type = "kimi"
remote_api_key = "YOUR-API-KEY-HERE"
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

## 三、完整版

微信群里的 “茴香豆” 开启了全部功能：

* Serper 搜索及 SourceGraph 搜索增强
* 群聊图片、微信公众号解析
* 文本指代消歧
* 混合 LLM
* 知识库为 openmmlab 相关的 12 个 repo（1700 个文档），拒绝闲聊

请阅读以下话题：

- [参照 config-advanced.ini 配置提升效果](./docs/full_dev_zh.md)
- [使用 rag.py 标注 SFT 训练数据](./docs/rag_annotate_sft_data_zh.md)
- [群聊场景指代消歧训练](./sft)
- [使用 wkteam 微信接入，整合图片、公众号解析和指代消歧](./docs/add_wechat_commercial_zh.md)

# 🛠️ FAQ

1. 机器人太高冷/太嘴碎怎么办？

   - 把真实场景中，应该回答的问题填入`resource/good_questions.json`，应该拒绝的填入`resource/bad_questions.json`
   - 调整 `repodir` 中的文档，确保不包含场景无关内容

   重新执行 `feature_store` 来更新阈值和特征库。

   ⚠️ 如果你足够自信，也可以直接修改 config.ini 的 `reject_throttle` 数值，一般来说 0.5 是很高的值；0.2 过低。

2. 启动正常，但运行期间显存 OOM 怎么办？

   基于 transformers 结构的 LLM 长文本需要更多显存，此时需要对模型做 kv cache 量化，如 [lmdeploy 量化说明](https://github.com/InternLM/lmdeploy/blob/main/docs/zh_cn/quantization)。然后使用 docker 独立部署 Hybrid LLM Service。

3. 如何接入其他 local LLM / 接入后效果不理想怎么办？

   - 打开 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py)，增加新的 LLM 推理实现
   - 参照 [test_intention_prompt 和测试数据](./tests/test_intention_prompt.py)，针对新模型调整 prompt 和阈值，更新到 [worker.py](./huixiangdou/service/worker.py)

4. 响应太慢/网络请求总是失败怎么办？

   - 参考 [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) 增加指数退避重传
   - local LLM 替换为 [lmdeploy](https://github.com/internlm/lmdeploy) 等推理框架，而非原生的 huggingface/transformers

5. 机器配置低，GPU 显存不足怎么办？

   此时无法运行 local LLM，只能用 remote LLM 配合 text2vec 执行 pipeline。请确保 `config.ini` 只使用 remote LLM，关闭 local LLM

6. `No module named 'faiss.swigfaiss_avx2'` 问题修复:

   找到 faiss 的位置

   ```python
   import faiss
   print(faiss.__file__)
   # /root/.conda/envs/InternLM2_Huixiangdou/lib/python3.10/site-packages/faiss/__init__.py
   ```

   添加软链接

   ```Bash
   # cd your_python_path/site-packages/faiss
   cd /root/.conda/envs/InternLM2_Huixiangdou/lib/python3.10/site-packages/faiss/
   ln -s swigfaiss.py swigfaiss_avx2.py
   ```

7. 报错 `(500, 'Internal Server Error')`，意为 standalone 模式启动的 LLM 服务没访问到。按如下方式定位

   - 执行 `python3 -m huixiangdou.service.llm_server_hybrid` 确定 LLM 服务无报错，监听的端口和配置一致。检查结束后按 ctrl-c 关掉。
   - 检查 `config.ini` 中各种 TOKEN 书写正确。

8. 如果使用 `deepseek` 进行 remote llm 调用，出现 400 错误可能是因为安全审查；在 [huixiangdou/main.py](huixiangdou/main.py) 中修改 `queries = ['请问如何安装 mmpose ?']` 为其他问题即可正常运行。

# 🍀 致谢

- [KIMI](https://kimi.moonshot.cn/): 长文本 LLM，支持直接上传文件
- [BCEmbedding](https://github.com/netease-youdao/BCEmbedding): 中英双语特征模型
- [Langchain-ChatChat](https://github.com/chatchat-space/Langchain-Chatchat): Langchain 和 ChatGLM 的应用
- [GrabRedEnvelope](https://github.com/xbdcc/GrabRedEnvelope): 微信抢红包

# 📝 引用

```shell
@misc{kong2024huixiangdou,
      title={HuixiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
      author={Huanjun Kong and Songyang Zhang and Jiaying Li and Min Xiao and Jun Xu and Kai Chen},
      year={2024},
      eprint={2401.08772},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}

@misc{kong2024huixiangdoucr,
      title={HuixiangDou-CR: Coreference Resolution in Group Chats},
      author={Huanjun Kong},
      year={2024},
      eprint={2405.02817},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```
