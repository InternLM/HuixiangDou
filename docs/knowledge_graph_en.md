# Hybrid Knowledge Graph and Dense Retrieval

By integrating a hybrid knowledge graph with dense retrieval, the F1 score is improved by 2%. For a detailed explanation of the solution, see [Zhihu](). The essence of this approach is to **weight high-frequency words**.

This approach is perfectly compatible with the older version. Below are the steps.

## 1. Build Knowledge Graph

To reduce costs, we use silicon cloud qwen-1.5-110B to extract entity words, and `config.ini` already supports silicon cloud. The modification is as follows:

```bash
[llm.server]
..
remote_type = "siliconcloud"
remote_api_key = "sk-ducerXXXXX"
remote_llm_max_text_length = 40000
remote_llm_model = "alibaba/Qwen1.5-110B-Chat"
rpm = 1000
```

Assuming the knowledge base is still in the `repodir` directory, first establish the knowledge graph.
After completion, there will be `jsonl` and `pickle` files under `workdir/kg`, and you can test the query.

```bash
# About 40 mins
python3 -m huixiangdou.service.kg --build
python3 -m huixiangdou.service.kg --query "How to install mmpose?"
```

## 2. Visualization

You can use neo4j for visualization:
```bash
python3 -m huixiangdou.service.kg --dump-neo4j --neo4j-uri ${URI} --neo4j-user ${USER} --neo4j-passwd ${PWD}
```

For more usage, you can use `--help`
```bash
python3 -m huixiangdou.service.kg --help
```

## 3. Build Dense Retrieval Feature Library

This step is the `feature_store` in the README. Since you need to calculate the optimal threshold under hybrid retrieval, do not skip it.

```bash
python3 -m huixiangdou.service.feature_store
```

Test it.

```bash
python3 -m huixiangdou.main --standalone
```
