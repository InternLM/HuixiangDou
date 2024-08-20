English | [简体中文](README_zh.md)

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
  <a href="https://arxiv.org/abs/2405.02817" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-2405.02817%20-darkred?logo=arxiv&logoColor=white" />
  </a>
</div>

</div>

HuixiangDou is a **professional knowledge assistant** based on LLM.

Advantages:

1. Design three-stage pipelines of preprocess, rejection and response
  * `chat_in_group` copes with **group chat** scenario, answer user questions without message flooding, see [2401.08772](https://arxiv.org/abs/2401.08772), [2405.02817](https://arxiv.org/abs/2405.02817), [Hybrid Retrieval](./docs/knowledge_graph_en.md) and [Precision Report](./evaluation/)
  * `chat_with_repo` for **real-time streaming** chat
2. No training required, with CPU-only, 2G, 10G, 20G and 80G configuration
3. Offers a complete suite of Web, Android, and pipeline source code, industrial-grade and commercially viable

Check out the [scenes in which HuixiangDou are running](./huixiangdou-inside.md) and join [WeChat Group](resource/figures/wechat.jpg) to try AI assistant inside.

If this helps you, please give it a star ⭐

# 🔆 New Features

Our Web version has been released to [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), where you can create knowledge base, update positive and negative examples, turn on web search, test chat, and integrate into Feishu/WeChat groups. See [BiliBili](https://www.bilibili.com/video/BV1S2421N7mn) and [YouTube](https://www.youtube.com/watch?v=ylXrT-Tei-Y) !

- \[2024/08\] `chat_with_repo` [pipeline](./huixiangdou/service/parallel_pipeline.py) 👍
- \[2024/07\] Image and text retrieval & Removal of `langchain` 👍
- \[2024/07\] [Hybrid Knowledge Graph and Dense Retrieval](./docs/knowledge_graph_en.md) improve 1.7% F1 score 🎯
- \[2024/06\] [Evaluation of chunksize, splitter, and text2vec model](./evaluation) 🎯
- \[2024/05\] [wkteam WeChat access](./docs/add_wechat_commercial_zh.md), parsing image & URL, support coreference resolution
- \[2024/05\] [SFT LLM on NLP task, F1 increased by 29%](./sft/) 🎯
  <table>
      <tr>
          <td>🤗</td>
          <td><a href="https://huggingface.co/tpoisonooo/HuixiangDou-CR-LoRA-Qwen-14B">LoRA-Qwen1.5-14B</a></td>
          <td><a href="https://huggingface.co/tpoisonooo/HuixiangDou-CR-LoRA-Qwen-32B">LoRA-Qwen1.5-32B</a></td>
          <td><a href="https://huggingface.co/datasets/tpoisonooo/HuixiangDou-CR/tree/main">alpaca data</a></td>
          <td><a href="https://arxiv.org/abs/2405.02817">arXiv</a></td>
      </tr>
  </table>
- \[2024/04\] [RAG Annotation SFT Q&A Data and Examples](./docs/rag_annotate_sft_data_zh.md)
- \[2024/04\] Release [Web Front and Back End Service Source Code](./web) 👍
- \[2024/03\] New [Personal WeChat Integration](./docs/add_wechat_accessibility_zh.md) and [**Prebuilt APK**](https://github.com/InternLM/HuixiangDou/releases/download/v0.1.0rc1/huixiangdou-20240508.apk) !
- \[2024/02\] \[Experimental Feature\] [WeChat Group](https://github.com/InternLM/HuixiangDou/blob/main/resource/figures/wechat.jpg) Integration of multimodal to achieve OCR

# 📖 Support Status

<table align="center">
  <tbody>
    <tr align="center" valign="bottom">
      <td>
        <b>LLM</b>
      </td>
      <td>
        <b>File Format</b>
      </td>
      <td>
        <b>Retrieval Method</b>
      </td>
      <td>
        <b>Instant Messaging</b>
      </td>
      <td>
        <b>Preprocessing</b>
      </td>
    </tr>
    <tr valign="top">
      <td>

- [InternLM2/InternLM2.5](https://github.com/InternLM/InternLM)
- [Qwen/Qwen2](https://github.com/QwenLM/Qwen2)
- [puyu](https://internlm.openxlab.org.cn/)
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

- [Knowledge Graph](./docs/knowledge_graph_en.md)
- [Internet Search](./huixiangdou/service/web_search.py)
- [SourceGraph](https://sourcegraph.com)
- Image and text (only markdown)

</td>

<td>

- WeChat
- Lark

</td>

<td>

- [Coreference Resolution](https://arxiv.org/abs/2405.02817)

</td>

</tr>

</tbody>
</table>

# 📦 Hardware Requirements

The following are the GPU memory requirements for different features, the difference lies only in whether the **options are turned on**.

|              Configuration Example               | GPU mem Requirements |                                                                                   Description                                                                                   |                       Verified on Linux                        |
| :----------------------------------------------: | :------------------: | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
|         [config-cpu.ini](./config-cpu.ini)         |   -    | Use [siliconcloud](https://siliconflow.cn/) API <br/> for text only | ![](https://img.shields.io/badge/x86-passed-blue?style=for-the-badge) |
|         [config-2G.ini](./config-2G.ini)         |         2GB          | Use openai API (such as [kimi](https://kimi.moonshot.cn), [deepseek](https://platform.deepseek.com/usage) and [stepfun](https://platform.stepfun.com/) to search for text only | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |
| [config-multimodal.ini](./config-multimodal.ini) |         10GB         |                                                                Use openai API for LLM, image and text retrieval                                                                 | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
| \[Standard Edition\] [config.ini](./config.ini)  |         19GB         |                                                                    Local deployment of LLM, single modality                                                                     | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
|   [config-advanced.ini](./config-advanced.ini)   |         80GB         |                                                   local LLM, anaphora resolution, single modality, practical for WeChat group                                                   | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |

# 🔥 Running the Standard Edition

We take the standard edition (local running LLM, text retrieval) as an introduction example. Other versions are just different in configuration options.

## I. Download and install dependencies

[Click to agree to the BCE model agreement](https://huggingface.co/maidalun1020/bce-embedding-base_v1), log in huggingface

```shell
huggingface-cli login
```

Install dependencies

```bash
# parsing `word` format requirements
apt update
apt install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev
# python requirements
pip install -r requirements.txt
# For python3.8, install faiss-gpu instead of faiss
```

## II. Create knowledge base and ask questions

Use mmpose documents to build the mmpose knowledge base and filtering questions. If you have your own documents, just put them under `repodir`.

Copy and execute all the following commands (including the '#' symbol).

```shell
# Download the knowledge base, we only take the documents of mmpose as an example. You can put any of your own documents under `repodir`
cd HuixiangDou
mkdir repodir
git clone https://github.com/open-mmlab/mmpose    --depth=1 repodir/mmpose

# Save the features of repodir to workdir, and update the positive and negative example thresholds into `config.ini`
mkdir workdir
python3 -m huixiangdou.service.feature_store
```

After running, test with `python3 -m huixiangdou.main --standalone`. At this time, reply to mmpose related questions (related to the knowledge base), while not responding to weather questions.

```bash
python3 -m huixiangdou.main --standalone

+---------------------------+---------+----------------------------+-----------------+
|         Query             |  State  |         Part of Reply      |   References    |
+===========================+=========+============================+=================+
| How to install mmpose?    | success | To install mmpose, plea..  | installation.md |
--------------------------------------------------------------------------------------
| How is the weather today? | unrelated.. | ..                     |                 |
+-----------------------+---------+--------------------------------+-----------------+
🔆 Input your question here, type `bye` for exit:
..
```

> \[!NOTE\]
>
> <div align="center">
> If restarting LLM every time is too slow, first <b>python3 -m huixiangdou.service.llm_server_hybrid</b>; then open a new window, and each time only execute <b>python3 -m huixiangdou.main</b> without restarting LLM.
> </div>

<br/>

💡 Also run a simple Web UI with `gradio`:

```bash
python3 -m huixiangdou.gradio
```

https://github.com/user-attachments/assets/9e5dbb30-1dc1-42ad-a7d4-dc7380676554

Or run a server to listen 23333, default pipeline is `chat_with_repo`:
```bash
python3 -m huixiangdou.server

# test async API 
curl -X POST http://127.0.0.1:23333/huixiangdou_stream  -H "Content-Type: application/json" -d '{"text": "how to install mmpose","image": ""}'
# cURL sync API
curl -X POST http://127.0.0.1:23333/huixiangdou_inference  -H "Content-Type: application/json" -d '{"text": "how to install mmpose","image": ""}'
```


Please update the `repodir` documents, [good_questions](./resource/good_questions.json) and [bad_questions](./resource/bad_questions.json), and try your own domain knowledge (medical, financial, power, etc.).

## III. Integration into Feishu, WeChat group

- [**One-way** sending to Feishu group](./docs/send_only_lark_group_zh.md)
- [**Two-way** Feishu group receiving and sending, recalling](./docs/add_lark_group_zh.md)
- [Personal WeChat Android access](./docs/add_wechat_accessibility_zh.md)
- [Personal WeChat wkteam access](./docs/add_wechat_commercial_zh.md)

## IV. Deploy web front and back end

We provide `typescript` front-end and `python` back-end source code:

- Multi-tenant management supported
- Zero programming access to Feishu and WeChat
- k8s friendly

Same as [OpenXlab APP](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), please read the [web deployment document](./web/README.md).

# 🍴 Other Configurations

## **CPU-only Edition**

If there is no GPU available, model inference can be completed using the [siliconcloud](https://siliconflow.cn/) API.

Taking docker miniconda+Python3.11 as an example, install CPU dependencies and run:

```bash
# Start container
docker run -v /path/to/huixiangdou:/huixiangdou -p 7860:7860 -p 23333:23333 -it continuumio/miniconda3 /bin/bash
# Install dependencies
apt update
apt install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev
python3 -m pip install -r requirements-cpu.txt
# Establish knowledge base
python3 -m huixiangdou.service.feature_store --config_path config-cpu.ini
# Q&A test
python3 -m huixiangdou.main --standalone --config_path config-cpu.ini
# gradio UI
python3 -m huixiangdou.gradio --config_path config-cpu.ini
```

If you find the installation too slow, a pre-installed image is provided in [Docker Hub](https://hub.docker.com/repository/docker/tpoisonooo/huixiangdou/tags). Simply replace it when starting the docker.

## **2G Cost-effective Edition**

If your GPU mem exceeds 1.8G, or you pursue cost-effectiveness. This configuration discards the local LLM and uses remote LLM instead, which is the same as the standard edition.

Take `siliconcloud` as an example, fill in the API TOKEN applied from the [official website](https://siliconflow.cn/) into `config-2G.ini`

```toml
# config-2G.ini
[llm]
enable_local = 0   # Turn off local LLM
enable_remote = 1  # Only use remote
..
remote_type = "siliconcloud"   # Choose siliconcloud
remote_api_key = "YOUR-API-KEY-HERE" # Your API key
remote_llm_model = "alibaba/Qwen1.5-110B-Chat"
```

> \[!NOTE\]
>
> <div align="center">
> Each Q&A scenario requires calling the LLM 7 times at worst, subject to the free user RPM limit, you can modify the <b>rpm</b> parameter in config.ini
> </div>

Execute the following to get the Q&A results

```shell
python3 -m huixiangdou.main --standalone --config-path config-2G.ini # Start all services at once
```

## **10G Multimodal Edition**

If you have 10G GPU mem, you can further support image and text retrieval. Just modify the model used in config.ini.

```toml
# config-multimodal.ini
# !!! Download `https://huggingface.co/BAAI/bge-visualized/blob/main/Visualized_m3.pth`    to `bge-m3` folder !!!
embedding_model_path = "BAAI/bge-m3"
reranker_model_path = "BAAI/bge-reranker-v2-minicpm-layerwise"
```

Note:

- You need to manually download [Visualized_m3.pth](https://huggingface.co/BAAI/bge-visualized/blob/main/Visualized_m3.pth) to the [bge-m3](https://huggingface.co/BAAI/bge-m3) directory
- Install FlagEmbedding on main branch, we have made [bugfix](https://github.com/FlagOpen/FlagEmbedding/commit/3f84da0796d5badc3ad519870612f1f18ff0d1d3). [Here](https://github.com/FlagOpen/FlagEmbedding/blob/master/FlagEmbedding/visual/eva_clip/bpe_simple_vocab_16e6.txt.gz) you can download `bpe_simple_vocab_16e6.txt.gz` 
- Install [requirments-multimodal.txt](./requirements-multimodal.txt)

Run gradio to test, see the image and text retrieval result [here](https://github.com/InternLM/HuixiangDou/pull/326).

```bash
python3 tests/test_query_gradio.py
```

## **80G Complete Edition**

The "HuiXiangDou" in the WeChat experience group has enabled all features:

- Serper search and SourceGraph search enhancement
- Group chat images, WeChat public account parsing
- Text coreference resolution
- Hybrid LLM
- Knowledge base is related to openmmlab's 12 repositories (1700 documents), refusing small talk

Please read the following topics:

- [Hybrid knowledge graph and dense retrieval](./docs/knowledge_graph_en.md)
- [Refer to config-advanced.ini configuration to improve effects](./docs/full_dev_en.md)
- [Group chat scenario anaphora resolution training](./sft)
- [Use wkteam WeChat access, integrate images, public account parsing, and anaphora resolution](./docs/add_wechat_commercial_zh.md)
- [Use rag.py to annotate SFT training data](./docs/rag_annotate_sft_data_zh.md)

## **Android Tools**

Contributors have provided [Android tools](./android) to interact with WeChat. The solution is based on system-level APIs, and in principle, it can control any UI (not limited to communication software).

# 🛠️ FAQ

1. What if the robot is too cold/too chatty?

   - Fill in the questions that should be answered in the real scenario into `resource/good_questions.json`, and fill the ones that should be rejected into `resource/bad_questions.json`.
   - Adjust the theme content in `repodir` to ensure that the markdown documents in the main library do not contain irrelevant content.

   Re-run `feature_store` to update thresholds and feature libraries.

   ⚠️ You can directly modify `reject_throttle` in config.ini. Generally speaking, 0.5 is a high value; 0.2 is too low.

2. Launch is normal, but out of memory during runtime?

   LLM long text based on transformers structure requires more memory. At this time, kv cache quantization needs to be done on the model, such as [lmdeploy quantization description](https://github.com/InternLM/lmdeploy/blob/main/docs/en/quantization). Then use docker to independently deploy Hybrid LLM Service.

3. How to access other local LLM / After access, the effect is not ideal?

   - Open [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py), add a new LLM inference implementation.
   - Refer to [test_intention_prompt and test data](./tests/test_intention_prompt.py), adjust prompt and threshold for the new model, and update them into [prompt.py](./huixiangdou/service/prompt.py).

4. What if the response is too slow/request always fails?

   - Refer to [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) to add exponential backoff and retransmission.
   - Replace local LLM with an inference framework such as [lmdeploy](https://github.com/internlm/lmdeploy), instead of the native huggingface/transformers.

5. What if the GPU memory is too low?

   At this time, it is impossible to run local LLM, and only remote LLM can be used in conjunction with text2vec to execute the pipeline. Please make sure that `config.ini` only uses remote LLM and turn off local LLM.


# 🍀 Acknowledgements

- [KIMI](https://kimi.moonshot.cn/): Long text LLM, supports direct file upload
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding): BAAI RAG group
- [BCEmbedding](https://github.com/netease-youdao/BCEmbedding): Chinese-English bilingual feature model
- [Langchain-ChatChat](https://github.com/chatchat-space/Langchain-Chatchat): Application of Langchain and ChatGLM
- [GrabRedEnvelope](https://github.com/xbdcc/GrabRedEnvelope): WeChat red packet grab

# 📝 Citation

````shell
@misc{kong2024huixiangdou,
      title={HuiXiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
      author={Huanjun Kong and Songyang Zhang and Jiaying Li and Min Xiao and Jun Xu and Kai Chen},
      year={2024},
      eprint={2401.08772},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}

@misc{kong2024huixiangdoucr,
      title={HuiXiangDou-CR: Coreference Resolution in Group Chats},
      author={Huanjun Kong},
      year={2024},
      eprint={2405.02817},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}```
````
