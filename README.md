# HuixiangDou
HuixiangDou: Overcoming Group Chat Scenarios with LLM-based Technical Assistance

## 体验入口

## 运行

我们将以 lmdeploy & mmpose 为例，介绍如何把知识助手部署到飞书群

1. 建立话题特征库
```bash
# 下载聊天话题
mkdir repodir && cd repodir # 
git clone https://github.com/openmmlab/mmpose --depth=1
git clone https://github.com/internlm/lmdeploy --depth=1

# 建立特征库
cd HuixiangDou && mkdir workdir # 创建工作目录
python3 -m pip install -r requirements.txt
python3 service/feature_store.py repodir workdir
```
运行结束后，茴香豆能够区分应该处理哪些用户话题，哪些闲聊应该拒绝。可以尝试自己的领域知识（如医疗，金融，电力等）
```bash
process "请问 mmdeploy 如何安装"
reject "茴香豆怎么做？"
```

2. 运行基础版技术助手

### 配置免费 TOKEN

茴香豆使用了搜索引擎，点击 获取限额免费 WEB_SEARCH_TOKEN。
查看 创建飞书机器人，获取回调 WEBHOOK_URL

把两个参数填入 config.ini
```shell

```

### 运行

请保证 GPU 显存超过 20GB（如 3090 及以上），若显存不足或没有 GPU，请参照 FAQ 修改。

首次运行将自动下载配置中的 internlm2-7B 和 text2vec-large-chinese，请保证网络畅通。

结束后，技术助手的答复将发送到飞书群。


1. 高级配置
config.ini 配置文件已包含参数说明。以下特性开启得越多，助手的闲聊拒绝能力、问题答复时机和答复质量越好：

### 使用更高精度 local LLM
调整 config.ini 中的`llm.local` 模型路径

### Hybrid LLM Service
对于支持 openai 接口的 LLM 服务，茴香豆可以发挥它的 Long Context 能力。
以下是 `config.ini` 配置示例：
```bash
..
[llm]
# 打开获取 token
..


# 打开申请白名单免费 token

```

### repo 搜索增强


## FAQ 

1. 如何接入其他 IM？
* 微信。企业微信请查看，；对于个人微信，请遵守《计算机安全保护法》。
* 钉钉。根据，仅 2022.06 前创建的内部群机器人可收发消息。

2. 显存 OOM 怎么办？


3. 没有 GPU怎么办？

* `requirements.txt` 中的 `faiss-gpu` 改成 `faiss-cpu`，安装 requirements.txt
* 确保 `config.ini` 使用 remote LLM，关闭 local LLM
* 运行时增加 `--cpu-only` 选项

    ```shell
    python3 lark_example workdir --cpu-only
    ```
