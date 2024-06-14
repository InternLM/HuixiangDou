# HuixiangDou Evaluation

## Rejection

用户输入问句，判断这句话和知识库是否有关。

这是个 NLP 分类问题。

输入：豆哥群聊所有句子，知识库使用 openmmlab 相关 repo

输出：不同阈值、不同 chunksize 下的 F1 score 曲线

* GT 来自人工标注，评价标准：是否和 openmmlab repo 沾边（开集）
* 知识库不做人工清洗/筛选，直接取 repo 里的 markdown/txt/pdf/word 文件

## Intention
用户输入句子和上下文（可能只有句子），判断是否在发问/求助。

## Topic Extraction

## RAG
