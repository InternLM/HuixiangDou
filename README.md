<div align="center">
  <img src="resource/logo_blue.svg" width="550px"/>

<small> [简体中文](README_zh.md) | English </small>

[![GitHub license](https://img.shields.io/badge/license-BSD--3--Clause-brightgreen.svg?style=plastic)](./LICENSE)
![CI](https://img.shields.io/github/actions/workflow/status/internml/huixiangdou/lint.yml?branch=master&style=plastic)

</div>

"HuixiangDou" is a domain-specific knowledge assistant based on the LLM. Features:

1. Deal with complex scenarios like group chats, answer user questions without causing message flooding.
2. Propose an algorithm pipeline for answering technical questions.
3. Low deployment cost, only need the LLM model to meet 4 traits can answer most of the user's questions, see [technical report](./resource/HuixiangDou.pdf).

View [HuixiangDou inside](./huixiangdou-inside.md).

# 📦 Hardware Requirements

The following are the hardware requirements for running. It is suggested to follow this document, starting with the basic version and gradually experiencing advanced features.

|     Version      | GPU Memory Requirements |                      Features                      |                                Tested on Linux                                |
| :--------------: | :---------------------: | :------------------------------------------------: | :---------------------------------------------------------------------------: |
|  Basic Version   |          20GB           | Answer basic domain knowledge questions, zero cost | ![](https://img.shields.io/badge/3090%2024G-passed-blue?style=for-the-badge)  |
| Advanced Version |          40GB           |   Answer source code level questions, zero cost    | ![](https://img.shields.io/badge/A100%2080G-passed-blue?style=for-the-badge)  |
| Modified Version |           4GB           |     Using openai API, operation involves cost      | ![](https://img.shields.io/badge/1660ti%206G-passed-blue?style=for-the-badge) |

# 🔥 Run

We will take lmdeploy & mmpose as examples to explain how to deploy the knowledge assistant to Feishu group chat.

## STEP1. Establish Topic Feature Repository

Execute all the commands below (including the '#' symbol).

```shell
# Download the repo
git clone https://github.com/internlm/huixiangdou --depth=1 && cd huixiangdou

# Download chatting topics
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1 repodir/mmpose
git clone https://github.com/internlm/lmdeploy --depth=1 repodir/lmdeploy

# Build a feature store
mkdir workdir # create a working directory
python3 -m pip install -r requirements.txt # install dependencies, python3.11 needs `conda install conda-forge::faiss-gpu`
python3 -m huixiangdou.service.feature_store # save the features of repodir to workdir
```

The first run will automatically download the configuration of [text2vec-large-chinese](https://huggingface.co/GanymedeNil/text2vec-large-chinese), you can also manually download it and update model path in `config.ini`.

After running, HuixiangDou can distinguish which user topics should be dealt with and which chitchats should be rejected. Please edit [good_questions](./resource/good_questions.json) and [bad_questions](./resource/bad_questions.json), and try your own domain knowledge (medical, finance, electricity, etc.).

```shell
# Accept technical topics
process query: Does mmdeploy support mmtrack model conversion now?
process query: Are there any Chinese text to speech models?
# Reject chitchat
reject query: What to eat for lunch today?
reject query: How to make HuixiangDou?
```

## STEP2. Run Basic Technical Assistant

**Configure free TOKEN**

HuixiangDou uses a search engine. Click [Serper](https://serper.dev/api-key) to obtain a quota-limited TOKEN and fill it in `config.ini`.

```shell
# config.ini
..
[web_search]
x_api_key = "${YOUR-X-API-KEY}"
..
```

**Test Q&A Effect**

Please ensure that the GPU memory is over 20GB (such as 3090 or above). If the memory is low, please modify it according to the FAQ.

The first run will automatically download the configuration of internlm2-7B.

- **Non-docker users**. If you **don't** use docker environment, you can start all services at once.

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
  # Start LLM service
  python3 -m huixiangdou.service.llm_server_hybrid
  ```

  Open a new terminal, configure the host IP (**not** container IP) in `config.ini`, run

  ```shell
  # config.ini
  [llm]
  ..
  client_url = "http://10.140.24.142:8888/inference" # example

  python3 -m huixiangdou.main
  ```

## STEP3. Integrate into Feishu \[Optional\]

Click [Create a Feishu Custom Robot](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot) to get the WEBHOOK_URL callback, and fill it in the config.ini.

```shell
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

If you still need to read Feishu group messages, see [Feishu Developer Square - Add Application Capabilities - Robots](https://open.feishu.cn/app?lang=zh-CN).

## STEP4. Advanced Version \[Optional\]

The basic version may not perform well. You can enable these features to enhance performance. The more features you turn on, the better.

1. Use higher accuracy local LLM

   Adjust the `llm.local` model in config.ini to `internlm2-20B`.
   This option has a significant effect, but requires more GPU memory.

2. Hybrid LLM Service

   For LLM services that support the openai interface, HuixiangDou can utilize its Long Context ability.
   Using [kimi](https://platform.moonshot.cn/) as an example, below is an example of `config.ini` configuration:

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

   We also support chatgpt API. Note that this feature will increase response time and operating costs.

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

     ```shell
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

# 🛠️ FAQ

1. How to access other IMs?

   - WeChat. For Enterprise WeChat, see [Enterprise WeChat Application Development Guide](https://developer.work.weixin.qq.com/document/path/90594) ; for personal WeChat, we have confirmed with the WeChat team that there is currently no API, you need to search and learn by yourself.
   - DingTalk. Refer to [DingTalk Open Platform-Custom Robot Access](https://open.dingtalk.com/document/robots/custom-robot-access)

2. What if the robot is too cold/too chatty?

   - Fill in the questions that should be answered in the real scenario into `resource/good_questions.json`, and fill the ones that should be rejected into `resource/bad_questions.json`.
   - Adjust the theme content in `repodir` to ensure that the markdown documents in the main library do not contain irrelevant content.

   Re-run `service/feature_store.py` to update thresholds and feature libraries.

3. Launch is normal, but out of memory during runtime?

   LLM long text based on transformers structure requires more memory. At this time, kv cache quantization needs to be done on the model, such as [lmdeploy quantization description](https://github.com/InternLM/lmdeploy/blob/main/docs/en/kv_int8.md). Then use docker to independently deploy Hybrid LLM Service.

4. How to access other local LLM / After access, the effect is not ideal?

   - Open [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py), add a new LLM inference implementation.
   - Refer to [test_intention_prompt and test data](./tests/test_intention_prompt.py), adjust prompt and threshold for the new model, and update them into [worker.py](./huixiangdou/service/worker.py).

5. What if the response is too slow/request always fails?

   - Refer to [hybrid llm service](./huixiangdou/service/llm_server_hybrid.py) to add exponential backoff and retransmission.
   - Replace local LLM with an inference framework such as [lmdeploy](https://github.com/internlm/lmdeploy), instead of the native huggingface/transformers.

6. What if the GPU memory is too low?

   At this time, it is impossible to run local LLM, and only remote LLM can be used in conjunction with text2vec to execute the pipeline. Please make sure that `config.ini` only uses remote LLM and turn off local LLM.

# 📝 Citation

```shell
@misc{2023HuixiangDou,
    title={HuixiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance},
    author={HuixiangDou Contributors},
    howpublished = {\url{https://github.com/internlm/huixiangdou}},
    year={2023}
}
```
