# HuixiangDou

# 运行

我们将以 lmdeploy & mmpose 为例，介绍如何把知识助手部署到飞书群

## 1. 建立话题特征库
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
运行结束后，茴香豆能够区分应该处理哪些用户话题，哪些闲聊应该拒绝。请尝试自己的领域知识（医疗，金融，电力等）
```bash
# 接受技术话题
process query: mmdeploy 现在支持 mmtrack 模型转换了么
process query: 有啥中文的 text to speech 模型吗?
# 拒绝闲聊
reject query: 今天中午吃什么？
reject query: 茴香豆是怎么做的
```

## 2. 基础版技术助手

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

请保证 GPU 显存超过 20GB（如 3090 及以上）。

首次运行将自动下载配置中的 internlm2-7B 和 text2vec-large-chinese，请保证网络畅通。

  * **非 docker 用户**。如果你**不**使用 docker 环境，可以一次启动所有服务。
    ```bash
    # standalone
    python3 main.py workdir --standalone
    ..

    ```

  * **docker 用户**。如果你正在使用 docker，`HuixiangDou` 的 Hybrid LLM Service 分离部署。
    ```bash
    # 启动服务
    python3 service/llm_server_hybride.py
    ```
    把 host IP 配置进 `config.ini`

    ```bash
    # config.ini
    [llm]
    ..
    client_url = "http://10.140.24.142:39999/inference" # 举例

    # 打开新终端，运行 main
    python3 main.py workdir
    ..
    ErrorCode.SUCCESS, 要安装 MMDeploy，首先需要准备一个支持 Python 3.6+ 和 PyTorch 1.8+ 的环境。然后，可以通过以下步骤安装 MMDeploy：
    ```

**[可选]集成到飞书**

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

如果还需要读取飞书群消息，见[飞书开发者广场-添加应用能力-机器人](https://open.feishu.cn/app?lang=zh-CN)。

![](./resource/lark-example.png)

# 高级配置
以下特性开启得越多，助手的闲聊拒绝能力、问题答复时机和答复质量越好：

1. 使用更高精度 local LLM

    调整 config.ini 中的`llm.local` 模型路径

2. Hybrid LLM Service

    对于支持 openai 接口的 LLM 服务，茴香豆可以发挥它的 Long Context 能力。
    以下是 `config.ini` 配置示例：

    ```bash
    ..
    [llm]
    # 打开获取 token
    ..

    # 打开申请白名单免费 token

    ```

3. repo 搜索增强


## FAQ 

1. 如何接入其他 IM ？
    * 微信。企业微信请查看，；对于个人微信，我们已向微信团队确认暂无正式 API。
    * 钉钉。根据，仅 2022.06 前创建的内部群机器人可收发消息。

2. 机器人太高冷/太嘴碎怎么办？

    把真实场景中，应该回答的问题填入`resource/good_questions.json`，应该拒绝的填入`resource/bad_questions.json`，重新执行 `service/feature_store.py`。

3. 运行期间显存 OOM 怎么办？

    基于 transformers 结构的 LLM 长文本需要更多显存，此时需要对模型做 kv cache 量化。如 [lmdeploy 量化说明](https://github.com/InternLM/lmdeploy/blob/main/docs/en/kv_int8.md)。

4. 没有 GPU怎么办？

    * `requirements.txt` 中的 `faiss-gpu` 改成 `faiss-cpu`，安装 requirements.txt
    * 确保 `config.ini` 使用 remote LLM，关闭 local LLM
    * 运行时增加 `--cpu-only` 选项

        ```shell
        python3 lark_example workdir --cpu-only
        ```
