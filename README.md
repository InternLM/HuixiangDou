
# 🎚️ Upgrade

[HuixiangDou2](https://github.com/tpoisonooo/HuixiangDou2) is a validated GraphRAG solution in the plant field. If you are interested in **non-computer fields**, try the new version.

---

English | [简体中文](README_zh.md)

<div align="center">

<img src="resource/logo_black.svg" width="555px"/>

<div align="center">
  <a href="https://cdn.vansin.top/internlm/dou.jpg" target="_blank">
    <img alt="Wechat" src="https://img.shields.io/badge/wechat-robot%20inside-brightgreen?logo=wechat&logoColor=white" />
  </a>
  <a href="https://huixiangdou.readthedocs.io/en/latest/" target="_blank">
    <img alt="Readthedocs" src="https://img.shields.io/badge/readthedocs-chat%20with%20AI-brightgreen?logo=readthedocs&logoColor=white" />
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

HuixiangDou1 is a **professional knowledge assistant** based on LLM.

Advantages:

1. Design three-stage pipelines of preprocess, rejection and response
    * `chat_in_group` copes with **group chat** scenario, answer user questions without message flooding, see [2401.08772](https://arxiv.org/abs/2401.08772), [2405.02817](https://arxiv.org/abs/2405.02817), [Hybrid Retrieval](./docs/en/doc_knowledge_graph.md) and [Precision Report](./evaluation/)
    * `chat_with_repo` for **real-time streaming** chat
2. No training required, with CPU-only, 2G, 10G   configuration
3. Offers a complete suite of Web, Android, and pipeline source code, industrial-grade and commercially viable

Check out the [scenes in which HuixiangDou are running](./huixiangdou-inside.md) and current public service status:
- [readthedocs ChatWithAI](https://huixiangdou.readthedocs.io/zh-cn/latest/) (cpu-only) is available
- [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web) is using GPU and under continuous maintenance
- [WeChat bot](https://cdn.vansin.top/internlm/dou.jpg) has a cost associated with WeChat integration. All code has been verified to be functional for one year. Please deploy it on your own for either the [free](https://github.com/InternLM/HuixiangDou/blob/main/docs/zh/doc_add_wechat_accessibility.md) or [commercial](https://github.com/InternLM/HuixiangDou/blob/main/docs/zh/doc_add_wechat_commercial.md) version.

If this helps you, please give it a star ⭐

# 🔆 New Features

Our Web version has been released to [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), where you can create knowledge base, update positive and negative examples, turn on web search, test chat, and integrate into Feishu/WeChat groups. See [BiliBili](https://www.bilibili.com/video/BV1S2421N7mn) and [YouTube](https://www.youtube.com/watch?v=ylXrT-Tei-Y) !

The Web version's API for Android also supports other devices. See [Python sample code](./tests/test_openxlab_android_api.py).

- \[2025/03\] Simplify deployment and removing `--standalone`
- \[2025/03\] [Forwarding multiple wechat group message](./docs/zh/doc_merge_wechat_group.md)
- \[2024/09\] [Inverted indexer](https://github.com/InternLM/HuixiangDou/pull/387) makes LLM prefer knowledge base🎯
- \[2024/09\] [Code retrieval](./huixiangdou/service/parallel_pipeline.py)
- \[2024/08\] [chat_with_readthedocs](https://huixiangdou.readthedocs.io/en/latest/), see [how to integrate](./docs/zh/doc_add_readthedocs.md) 👍
- \[2024/07\] Image and text retrieval & Removal of `langchain` 👍
- \[2024/07\] [Hybrid Knowledge Graph and Dense Retrieval](./docs/en/doc_knowledge_graph.md) improve 1.7% F1 score 🎯
- \[2024/06\] [Evaluation of chunksize, splitter, and text2vec model](./evaluation) 🎯
- \[2024/05\] [wkteam WeChat access](./docs/zh/doc_add_wechat_commercial.md), parsing image & URL, support coreference resolution
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
- \[2024/04\] [RAG Annotation SFT Q&A Data and Examples](./docs/zh/doc_rag_annotate_sft_data.md)
- \[2024/04\] Release [Web Front and Back End Service Source Code](./web) 👍
- \[2024/03\] New [Personal WeChat Integration](./docs/zh/doc_add_wechat_accessibility.md) and [**Prebuilt APK**](https://github.com/InternLM/HuixiangDou/releases/download/v0.1.0rc1/huixiangdou-20240508.apk) !
- \[2024/02\] \[Experimental Feature\] [WeChat Group](https://cdn.vansin.top/internlm/dou.jpg) Integration of multimodal to achieve OCR

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
        <b>Integration</b>
      </td>
      <td>
        <b>Preprocessing</b>
      </td>
    </tr>
    <tr valign="top">
      <td>

- [DeepSeek](https://www.deepseek.com)
- [InternLM](https://internlm.intern-ai.org.cn)
- [GLM](https://www.zhipuai.cn)
- [KIMI](https://kimi.moonshot.cn)
- [StepFun](https://platform.stepfun.com)
- [vLLM](https://github.com/vllm-project/vllm)
- [Silicon🏷️](https://cloud.siliconflow.cn/s/tpoisonooo)
- [PPIO🏷️](https://ppinfra.com/user/register?invited_by=7GF8QS) 
- [Xi-Api](https://api.xi-ai.cn)

</td>
<td>

- excel
- html
- markdown
- pdf
- ppt
- txt
- word

</td>

<td>

- Dense for Document
- Sparse for Code 
- [Knowledge Graph](./docs/en/doc_knowledge_graph.md)
- [Internet Search](./huixiangdou/service/web_search.py)
- [SourceGraph](https://sourcegraph.com)
- Image and Text

</td>

<td>

- WeChat([android](./docs/zh/doc_add_wechat_accessibility.md)/[wkteam](./docs/zh/doc_add_wechat_commercial.md))
- Lark
- [OpenXLab Web](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web)
- [Gradio Demo](./huixiangdou/gradio_ui.py)
- [HTTP Server](./huixiangdou/api_server.py)
- [Read the Docs](./docs/zh/doc_add_readthedocs.md)

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
|   \[Standard Edition\][config.ini](./config.ini)         |         2GB          | Use openai API (such as [kimi](https://kimi.moonshot.cn), [deepseek](https://platform.deepseek.com/usage) and [stepfun](https://platform.stepfun.com/) to search for text only | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |
| [config-multimodal.ini](./config-multimodal.ini) |         10GB         |                                                                Use openai API for LLM, image and text retrieval                                                                 | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |

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

## II. Create knowledge base

We use some novels to build knowledge base and filtering questions. If you have your own documents, just put them under `repodir`.

Copy and execute all the following commands (including the '#' symbol).

```shell
# Download the knowledge base, we only take the some documents as example. You can put any of your own documents under `repodir`
cd HuixiangDou
mkdir repodir
cp -rf resource/data* repodir/

# Build knowledge base, this will save the features of repodir to workdir, and update the positive and negative example thresholds into `config.ini`
mkdir workdir
python3 -m huixiangdou.services.store
```

## III. Setup LLM API and test
Set the model and `api-key` in `config.ini`. If running LLM locally, we recommend using `vllm`.

```text
vllm serve /path/to/Qwen-2.5-7B-Instruct --enable-prefix-caching --served-model-name Qwen-2.5-7B-Instruct
```

Here is an example of the configured `config.ini`:

```ini
[llm.server]
remote_type = "kimi"
remote_api_key = "sk-dp3GriuhhLXnYo0KUuWbFUWWKOXXXXXXXXXX"
remote_llm_model = "auto"

# remote_type = "step"
# remote_api_key = "5CpPyYNPhQMkIzs5SYfcdbTHXq3a72H5XXXXXXXXXXXXX"
# remote_llm_model = "auto"

# remote_type = "deepseek"
# remote_api_key = "sk-86db9a205aa9422XXXXXXXXXXXXXX"
# remote_llm_model = "deepseek-chat"

# remote_type = "vllm"
# remote_api_key = "EMPTY"
# remote_llm_model = "Qwen2.5-7B-Instruct"

# remote_type = "siliconcloud"
# remote_api_key = "sk-xxxxxxxxxxxxx"
# remote_llm_model = "alibaba/Qwen1.5-110B-Chat"

# remote_type = "ppio"
# remote_api_key = "sk-xxxxxxxxxxxxx"
# remote_llm_model = "thudm/glm-4-9b-chat"
```

Then run the test:

```text
# Respond to questions related to the Hundred-Plant Garden (related to the knowledge base), but do not respond to weather questions.
python3 -m huixiangdou.main

+-----------------------+---------+--------------------------------+-----------------+
|         Query         |  State  |         Reply                  |   References    |
+=======================+=========+================================+=================+
| What is in the Hundred-Plant Garden? | success | The Hundred-Plant Garden has a rich variety of natural landscapes and life... | installation.md |
--------------------------------------------------------------------------------------
| How is the weather today?         | Init state| ..                           |                 |
+-----------------------+---------+--------------------------------+-----------------+
🔆 Input your question here, type `bye` for exit:
..
```

💡 Also run a simple Web UI with `gradio`:

```bash
python3 -m huixiangdou.gradio_ui
```

<video src="https://github.com/user-attachments/assets/9e5dbb30-1dc1-42ad-a7d4-dc7380676554" ></video>

Or run a server to listen 23333, default pipeline is `chat_with_repo`:
```bash
python3 -m huixiangdou.api_server

# test async API 
curl -X POST http://127.0.0.1:23333/huixiangdou_stream  -H "Content-Type: application/json" -d '{"text": "how to install mmpose","image": ""}'
# cURL sync API
curl -X POST http://127.0.0.1:23333/huixiangdou_inference  -H "Content-Type: application/json" -d '{"text": "how to install mmpose","image": ""}'
```


Please update the `repodir` documents, [good_questions](./resource/good_questions.json) and [bad_questions](./resource/bad_questions.json), and try your own domain knowledge (medical, financial, power, etc.).

## IV. Integration

### To Feishu, WeChat group

- [**One-way** sending to Feishu group](./docs/zh/doc_send_only_lark_group.md)
- [**Two-way** Feishu group receiving and sending, recalling](./docs/zh/doc_add_lark_group.md)
- [Personal WeChat Android access](./docs/zh/doc_add_wechat_accessibility.md) and [Android tool](./android)
- [Personal WeChat wkteam access](./docs/zh/doc_add_wechat_commercial.md)

### To web front and backend

We provide `typescript` front-end and `python` back-end source code:

- Multi-tenant management supported
- Zero programming access to Feishu and WeChat
- k8s friendly

Same as [OpenXlab APP](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), please read the [web deployment document](./web/README.md).

### To readthedocs.io

[Try right-bottom button on the page](https://huixiangdou.readthedocs.io/zh-cn/latest/) and [document](./docs/zh/doc_add_readthedocs.md).

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
python3 -m huixiangdou.services.store --config_path config-cpu.ini
# Q&A test
python3 -m huixiangdou.main --config_path config-cpu.ini
# gradio UI
python3 -m huixiangdou.gradio_ui --config_path config-cpu.ini
```

If you find the installation too slow, a pre-installed image is provided in [Docker Hub](https://hub.docker.com/repository/docker/tpoisonooo/huixiangdou/tags). Simply replace it when starting the docker.

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
- Install [requirements/multimodal.txt](./requirements/multimodal.txt)

Run gradio to test, see the image and text retrieval result [here](https://github.com/InternLM/HuixiangDou/pull/326).

```bash
python3 tests/test_query_gradio.py
```

## **Furthermore**

Please read the following topics:

- [Hybrid knowledge graph and dense retrieval](./docs/en/doc_knowledge_graph.md)
- [Refer to config-advanced.ini configuration to improve effects](./docs/en/doc_full_dev.md)
- [Group chat scenario anaphora resolution training](./sft)
- [Use wkteam WeChat access, integrate images, public account parsing, and anaphora resolution](./docs/zh/doc_add_wechat_commercial.md)
- [Use rag.py to annotate SFT training data](./docs/zh/doc_rag_annotate_sft_data.md)

# 🛠️ FAQ

1. What if the robot is too cold/too chatty?

   - Fill in the questions that should be answered in the real scenario into `resource/good_questions.json`, and fill the ones that should be rejected into `resource/bad_questions.json`.
   - Adjust the theme content in `repodir` to ensure that the markdown documents in the main library do not contain irrelevant content.

   Re-run `feature_store` to update thresholds and feature libraries.

   ⚠️ You can directly modify `reject_throttle` in config.ini. Generally speaking, 0.5 is a high value; 0.2 is too low.

2. Launch is normal, but out of memory during runtime?

   LLM long text based on transformers structure requires more memory. At this time, kv cache quantization needs to be done on the model, such as [lmdeploy quantization description](https://github.com/InternLM/lmdeploy/blob/main/docs/en/quantization). Then use docker to independently deploy Hybrid LLM Service.

# 🍀 Acknowledgements

- [KIMI](https://kimi.moonshot.cn/): Long text LLM, supports direct file upload
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding): BAAI RAG group
- [BCEmbedding](https://github.com/netease-youdao/BCEmbedding): Chinese-English bilingual feature model
- [Langchain-ChatChat](https://github.com/chatchat-space/Langchain-Chatchat): Application of Langchain and ChatGLM
- [GrabRedEnvelope](https://github.com/xbdcc/GrabRedEnvelope): WeChat red packet grab

# 📝 Citation

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
