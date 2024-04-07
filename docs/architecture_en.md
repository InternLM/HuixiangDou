# Code Structure Explanation

This document primarily explains the directory structure and functionalities of HuixiangDou. The documentation may not be updated in real-time with the code, but the definitions that are in place will no longer change.

## First Layer: Project Introduction

The outermost layer of the project contains only the huixiangdou python module and one configuration file.

```bash
.
├── config-advanced.ini
├── config-2G.ini # Advanced and Experience version configuration examples, slightly modified `config.ini`
├── config.ini # Basic configuration example, containing all options and parameters of the algorithm
..
├── huixiangdou # python module
..
├── requirements-lark-group.txt # Dependencies needed only for Lark group integration
├── requirements.txt # Basic dependencies
```

The configuration is actually in toml format, but to avoid unfamiliarity for users, it was renamed to the commonly seen .ini in Windows.

## Second Layer: huixiangdou Module

The module contains only 3 parts:

```bash
.
├── frontend # Frontends like Lark, WeChat, etc., are part of the algorithm
├── main.py # main provides an example program
├── service # service is the implementation of the algorithm
```

**service** In our [paper](https://arxiv.org/abs/2401.08772), we introduced HuixiangDou as a pipeline structure; in implementation, it may include functions, a local LLM, or an RPC. All these foundational capabilities are regarded as services.

**frontend** Since HuixiangDou is a set of algorithmic pipelines, things like WeChat, Lark, and the web are its frontends. This directory contains utility classes and functions that call the frontend, currently with Lark's API usage.

**main.py** Now with algorithms and a frontend, we need an entry function to implement the business logic. If you configured Lark in your `config.ini`, you should send your queries there, qaq.

## Third Layer: Service

This is where the main body of the HuixiangDou pipeline is.

```bash
.
├── feature_store.py # Manages the creation and query of text features. In the future, "creation" and "query" will be separated
├── helper.py # Contains some helper tools
├── llm_client.py # LLM might be an RPC, so a client is needed
├── llm_server_hybrid.py # There might be more than one LLM, hence the name hybrid
├── sg_search.py # Sourcegraph client
├── web_search.py # Client for Google search
└── worker.py # The main logic as mentioned in the paper, calling the components above
```

**1. feature_store.py** In the era of facial recognition, the storage and retrieval of facial features are called a feature store, which is the origin of the name.

1. When extracting features, the text will be partitionally split (the construction technique affects accuracy), the text2vec model extracts features, and saves them locally;
2. During retrieval, in addition to directly using text2vec matching, a re-rank model will adjust the order
   The feature store simply acts as a "guidepost" in the entire pipeline and doesn't rely on chunks to provide answers.

**2. llm part** It includes both client and server_hybrid because:

1. The model could be deployed locally or be an OpenAI interface.
2. Each LLM has its unique features; we want them to be cost-effective without losing functionality. Thus, it employs "on-demand calling," hence the term `hybrid`.
3. Even for the same feature `topk=1`, configuration parameters vary by provider. The main logic doesn't handle these details; they are all implemented in llm_server_hybrid.py.

**3. Search** The LLMs' answers always require some ground truth. If the knowledge base does not suffice, relying on a search engine is a good choice.

The feature here is: **repeatedly checking the quality of Internet results**. Most online information is harmful, and using it directly without filtering can lead to incorrect responses or value issues.

**4. Search enhancement** The search capability of engines is limited, and the vast body of knowledge is infinite. “Looking for a needle in a haystack” is naturally challenging.

However, if you already know the answer lies within a certain repo, searching only that repo will surely improve accuracy. sg_search is designed to use the knowledge graph to find answers within a small repo, where "using a sledgehammer to crack a nut" can be effective.

**5. Main logic worker.py** After being "attacked" tens of thousands of times over half a year across multiple WeChat groups, a set of pipelines was summarized.
