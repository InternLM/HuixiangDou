English | [简体中文](README_zh.md)

<div align="center">

<img src="resource/logo_black.svg" width="500px"/>

<div align="center">
  <a href="resource/figures/wechat.jpg" target="_blank">
    <img alt="Wechat" src="https://img.shields.io/badge/wechat-assistant%20inside-brightgreen?logo=wechat&logoColor=white" />
  </a>
  <a href="https://arxiv.org/abs/2401.08772" target="_blank">
    <img alt="Arxiv" src="https://img.shields.io/badge/arxiv-paper%20-darkred?logo=arxiv&logoColor=white" />
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
</div>

</div>

"HuixiangDou" is a domain-specific knowledge assistant based on the LLM. Features:

1. Deal with complex scenarios like group chats, answer user questions without causing message flooding.
2. Propose an algorithm pipeline for answering technical questions.
3. Low deployment cost, only need the LLM model to meet 4 traits can answer most of the user's questions, see [arxiv2401.08772](https://arxiv.org/abs/2401.08772).

Check out the [scenes in which HuixiangDou are running](./huixiangdou-inside.md) and join [WeChat Group](resource/figures/wechat.jpg) to try AI assistant inside.

If this helps you, please give it a star ⭐

# 🔆 News

The web portal is available on [OpenXLab](https://openxlab.org.cn/apps/detail/tpoisonooo/huixiangdou-web), where you can build your own knowledge assistant without any coding, using WeChat and Feishu groups.

Visit web portal usage video on [YouTube](https://www.youtube.com/watch?v=ylXrT-Tei-Y) and [BiliBili](https://www.bilibili.com/video/BV1S2421N7mn).

- \[2024/03\] Support `ppt` and `html` file format
- \[2024/03\] Speedup `pdf` and table parsing for higher precision
- \[2024/03\] Support [zhipuai](https://zhipuai.cn) in `config.ini`
- \[2024/03\] New [wechat integration method](./docs/add_wechat_accessibility_zh.md) with [**prebuilt android apk**](https://github.com/InternLM/HuixiangDou/releases/download/v0.1.0rc1/huixiangdou-1.0.0.apk) !
- \[2024/03\] Support `pdf`/`word`/`excel` file format; reply referenced filename or web URL
- \[2024/02\] Add [BCEmbedding](https://github.com/netease-youdao/BCEmbedding) rerank for higher precision 👍
- \[2024/02\] [Support deepseek](https://github.com/InternLM/HuixiangDou/tree/main?tab=readme-ov-file#step2-run-basic-technical-assistant) and qwen1.5; automatically choose model depending on GPU
- \[2024/02\] \[experimental\] Integrated multimodal model into our [wechat group](https://github.com/InternLM/HuixiangDou/blob/main/resource/figures/wechat.jpg) for OCR
- \[2024/01\] Support [personal wechat](./docs/add_wechat_group_zh.md) and [lark group](./docs/add_lark_group_zh.md)

# 📦 Hardware Requirements

The following are the hardware requirements for running. It is suggested to follow this document, starting with the basic version and gradually experiencing advanced features.

|      Version       | GPU Memory Requirements |                                                                                               Features                                                                                               |                                Tested on Linux                                |
| :----------------: | :---------------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
| Experience Version |          1.5GB          | Use [openai API](https://pypi.org/project/openai/) (e.g., [kimi](https://kimi.moonshot.cn) and [deepseek](https://platform.deepseek.com)) to handle source code-level issues <br/> Free within quota | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |
|   Basic Version    |          19GB           |                                                                             Deploy local LLM can answer basic questions                                                                              | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
|  Advanced Version  |          40GB           |                                                                Fully utilizing search + long-text, answer source code-level questions                                                                | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |

# 🔥 Run

We will take mmpose and some `pdf`/`word`/`excel`/`ppt` examples to explain how to deploy the knowledge assistant to Feishu group chat.

## STEP1. Establish Topic Feature Repository

Huggingface login

```shell
huggingface-cli login
```

Execute all the commands below (including the '#' symbol).

```shell
# Download the repo
git clone https://github.com/internlm/huixiangdou --depth=1 && cd huixiangdou

# Download chatting topics
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1 repodir/mmpose
git clone https://github.com/tpoisonooo/huixiangdou-testdata --depth=1 repodir/testdata


# parsing `word` requirements
apt install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev
# python requirements
pip install -r requirements.txt

# save the features of repodir to workdir
mkdir workdir
python3 -m huixiangdou.service.feature_store
```

The first run will automatically download [text2vec model](./config.ini), you can also manually download it and update model path in `config.ini`.

After running, HuixiangDou can distinguish which user topics should be dealt with and which chitchats should be rejected. Please edit [good_questions](./resource/good_questions.json) and [bad_questions](./resource/bad_questions.json), and try your own domain knowledge (medical, finance, electricity, etc.).

```shell
# Reject chitchat
reject query: What to eat for lunch today?
reject query: How to make HuixiangDou?

# Accept technical topics
process query: How to install mmpose ?
process query: What should I pay attention to when using research instruments?
```

## STEP2. Run Basic Technical Assistant

**Configure free TOKEN**

HuixiangDou uses a search engine. Click [Serper](https://serper.dev/api-key) to obtain a quota-limited TOKEN and fill it in `config.ini`.

```ini
# config.ini
..
[web_search]
x_api_key = "${YOUR-X-API-KEY}"
..
```

**Test Q&A Effect**

\[Experience Version\] If your GPU memory is insufficient to locally run the 7B LLM (less than 15GB), try `kimi` or `deepseek` for [30 million free token](https://platform.deepseek.com/). See [config-experience.ini](./config-experience.ini)

```
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

By default, with `enable_local=1`, the LLM will be automatically downloaded on your first run depending on GPU.

- **Non-docker users**. If you **don't** use docker, you can start all services at once.

  ```shell
  # standalone
  python3 -m huixiangdou.main --standalone
  ..
  ErrorCode.SUCCESS,
  Query: Could you please advise if there is any good optimization method for video stream detection flickering caused by frame skipping?
  Reply:
  1. Frame rate control and frame skipping strategy are key to optimizing video stream detection performance, but you need to pay attention to the impact of frame skipping on detection results.
  2. Multithreading processing and caching mechanism can improve detection efficiency, but you need to pay attention to the stability of detection results.
  3. The use of sliding window method can reduce the impact of frame skipping and caching on detection results.
  ```

- **Docker users**. If you are using docker, HuixiangDou's Hybrid LLM Service needs to be deployed separately.

  ```shell
  # First start LLM service listening the port 8888
  python3 -m huixiangdou.service.llm_server_hybrid
  ..
  ======== Running on http://0.0.0.0:8888 ========
  (Press CTRL+C to quit)
  ```

  Then open a new docker container, configure the host IP (**not** container IP) in `config.ini`, and run `python3 -m huixiangdou.main`

  ```ini
  # config.ini
  [llm]
  ..
  client_url = "http://10.140.24.142:8888/inference" # example, use your real host IP here

  # run
  python3 -m huixiangdou.main
  ..
  ErrorCode.SUCCESS
  ```

## STEP3. Send to Feishu/Personal Wechat \[Optional\]

Click [Create a Feishu Custom Robot](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot) to get the WEBHOOK_URL callback, and fill it in the config.ini.

```ini
# config.ini
..
[frontend]
type = "lark"
webhook_url = "${YOUR-LARK-WEBHOOK-URL}"
```

Run. After it ends, the technical assistant's reply will be sent to the Feishu group chat.

```shell
python3 -m huixiangdou.main --standalone # for non-docker users
python3 -m huixiangdou.main # for docker users
```

<img src="./resource/figures/lark-example.png" width="400">

- [How to use the HuixiangDou Lark group chat to send and revert messages](./docs/add_lark_group_zh.md)
- Refer to the guide for [Personal Wechat Example](./docs/add_wechat_group_zh.md)
- You can also check [DingTalk Open Platform-Custom Robot Access](https://open.dingtalk.com/document/robots/custom-robot-access)

## STEP4. Advanced Version \[Optional\]

The basic version may not perform well. You can enable these features to enhance performance. The more features you turn on, the better.

1. Use higher accuracy local LLM

   Adjust the `llm.local` model in config.ini to `internlm2-chat-20b`.
   This option has a significant effect, but requires more GPU memory.

2. Hybrid LLM Service

   For LLM services that support the [openai](https://pypi.org/project/openai/) interface, HuixiangDou can utilize its Long Context ability.
   Using [kimi](https://platform.moonshot.cn/) as an example, below is an example of `config.ini` configuration:

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

   We also support chatgpt. Note that this feature will increase response time and operating costs.

3. Repo search enhancement

   This feature is suitable for handling difficult questions and requires basic development capabilities to adjust the prompt.

   - Click [sourcegraph-account-access](https://sourcegraph.com/users/tpoisonooo/settings/tokens) to get token

     ```shell
     # open https://github.com/sourcegraph/src-cli#installation
     sudo curl -L https://sourcegraph.com/.api/src-cli/src_linux_amd64 -o /usr/local/bin/src && chmod +x /usr/local/bin/src

     # Enable search and fill the token
     [worker]
     enable_sg_search = 1
     ..
     [sg_search]
     ..
     src_access_token = "${YOUR_ACCESS_TOKEN}"
     ```

   - Edit the name and introduction of the repo, we take opencompass as an example

     ```ini
     # config.ini
     # add your repo here, we just take opencompass and lmdeploy as example
     [sg_search.opencompass]
     github_repo_id = "open-compass/opencompass"
     introduction = "Used for evaluating large language models (LLM) .."
     ```

   - Use `python3 -m huixiangdou.service.sg_search` for unit test, the returned content should include opencompass source code and documentation

     ```shell
     python3 -m huixiangdou.service.sg_search
     ..
     "filepath": "opencompass/datasets/longbench/longbench_trivia_qa.py",
     "content": "from datasets import Dataset..
     ```

   Run `main.py`, HuixiangDou will enable search enhancement when appropriate.

4. Tune Parameters

   It is often unavoidable to adjust parameters with respect to business scenarios.

   - Refer to [data.json](./tests/data.json) to add real data, run [test_intention_prompt.py](./tests/test_intention_prompt.py) to get suitable prompts and thresholds, and update them into [worker](./huixiangdou/service/worker.py).
   - Adjust the [number of search results](./huixiangdou/service/worker.py) based on the maximum length supported by the model.
   - Update `web_search.domain_partial_order` in `config.ini` according to your scenarios.

# 🛠️ FAQ

1. What if the robot is too cold/too chatty?

   - Fill in the questions that should be answered in the real scenario into `resource/good_questions.json`, and fill the ones that should be rejected into `resource/bad_questions.json`.
   - Adjust the theme content in `repodir` to ensure that the markdown documents in the main library do not contain irrelevant content.

   Re-run `feature_store` to update thresholds and feature libraries.

2. Launch is normal, but out of memory during runtime?

   LLM long text based on transformers structure requires more memory. At this time, kv cache quantization needs to be done on the model, such as [lmdeploy quantization description](https://github.com/InternLM/lmdeploy/blob/main/docs/zh_cn/quantization/kv_int8.md). Then use docker to independently deploy Hybrid LLM Service.

3. How to access other local LLM / After access, the effect is not ideal?

   - Open [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py), add a new LLM inference implementation.
   - Refer to [test_intention_prompt and test data](./tests/test_intention_prompt.py), adjust prompt and threshold for the new model, and update them into [worker.py](./huixiangdou/service/worker.py).

4. What if the response is too slow/request always fails?

   - Refer to [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) to add exponential backoff and retransmission.
   - Replace local LLM with an inference framework such as [lmdeploy](https://github.com/internlm/lmdeploy), instead of the native huggingface/transformers.

5. What if the GPU memory is too low?

   At this time, it is impossible to run local LLM, and only remote LLM can be used in conjunction with text2vec to execute the pipeline. Please make sure that `config.ini` only uses remote LLM and turn off local LLM.

# 🍀 Acknowledgements

- [kimi-chat](https://kimi.moonshot.cn/): long context LLM
- [BCEmbedding](https://github.com/netease-youdao/BCEmbedding): Bilingual and Crosslingual Embedding (BCEmbedding) in English and Chinese
- [Langchain-ChatChat](https://github.com/chatchat-space/Langchain-Chatchat): ChatGLM Application based on Langchain
- [GrabRedEnvelope](https://github.com/xbdcc/GrabRedEnvelope): Grab Wechat RedEnvelope

# 📝 Citation

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
