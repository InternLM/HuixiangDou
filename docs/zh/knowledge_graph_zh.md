# 混合知识图谱和稠密检索

通过混合知识图谱和稠密检索，拒答 F1 提升约 2 个点，它的本质是**给高频词加权**。介绍已同步到[飞书](https://aicarrier.feishu.cn/docx/F51pduYyMof8syxKe5RchiU1nIN) 和[知乎](https://zhuanlan.zhihu.com/p/709589834)。

本方案对老版本完美兼容，以下是完整操作步骤。

## 一、建立知识图谱

为降低成本，我们使用 silicon cloud qwen-1.5-110B 提取实体词， `config.ini` 已支持 silicon cloud，修改片段如下：

```bash
[llm.server]
..
remote_type = "siliconcloud"
remote_api_key = "sk-ducerXXXXX"
remote_llm_max_text_length = 40000
remote_llm_model = "alibaba/Qwen1.5-110B-Chat"
rpm = 1000
```

假设知识库仍在 repodir 目录下，先建立知识图谱。
完成后， `workdir/kg` 下有 jsonl 和 pickle 文件，可简单测试 query 效果

```bash
# 大约 2 小时
python3 -m huixiangdou.service.kg --build
python3 -m huixiangdou.service.kg --query 如何安装mmpose?
..
+-----------------+-------+------------------------+---------------------------+
|      Query      | State |     Part of Reply      |        References         |
+=================+=======+========================+===========================+
| 如何安装mmpose?  | 0     | repodir/mmpose/READM.. |                           |
|                 |       |                        | <div align="center">      |
|                 |       |                        |   <img                    |
|                 |       |                        | src="resources/mmpose-    |
..
```

## 二、可视化

可以利用 neo4j 可视化：

```bash
python3 -m huixiangdou.service.kg --dump-neo4j --neo4j-uri ${URI} --neo4j-user ${USER} --neo4j-passwd ${PWD}
```

更多用法可以 `--help`

## 三、建立稠密检索特征库

这步就是 README 里的 `feature_store`，因为要算混合检索下的最佳阈值，不要跳过。

```bash
python3 -m huixiangdou.service.feature_store
```

测试效果

```bash
python3 -m huixiangdou.main --standalone
```

不同方法的精度对比表见 [evaluation](../evaluation/README_zh.md)
