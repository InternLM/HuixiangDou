# 高精度配置参考

标准版可能效果不佳，可开启以下特性来提升效果。配置模板请参照 [config-advanced.ini](../../config-advanced.ini)

1. repo 搜索增强

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

2. 调参

   针对业务场景调参往往不可避免。

   - 参照 [data.json](../../tests/data.json) 增加真实数据，运行 [test_intention_prompt.py](../../tests/test_intention_prompt.py) 得到合适的 prompt 和阈值，更新进 [prompt.py](../../huixiangdou/service/prompt.py)
   - 根据模型支持的最大长度，调整[搜索结果个数](../../huixiangdou/service/serial_pipeline.py)
   - 按照场景偏好，修改 config.ini 中的 `web_search.domain_partial_order`，即搜索结果偏序
