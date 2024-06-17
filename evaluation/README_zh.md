# HuixiangDou Evaluation

## 数据说明
input analyze count 1150, avg 5048.53, median 2912
0-7716  79.83%
7716-15432  14.00%
15432-23148  4.09%
23148-30864  0.70%
30864-38580  0.35%
38580-46296  0.35%
46296-54012  0.17%
54012-61728  0.09%
61728-69444  0.26%
69444-77160  0.09%
77160-84876  0.09%

## 阈值应该选多少

如果用 F1 做指标的话，和 BCE 作者结论一致，应该在 0.41 附近。

在这个业务场景里，优先高 recall（被拒的都是该拒的），阈值偏小（例如 0.3，保证 recall 大于 95%）

## 特征距离，应该选多大的 chunk size ?

?? 理想中， corpus `split_documents` 后的平均长度，应该和 text2vec 模型一致（例如 BCE 最大长度是 512）。
准确地说应该是 token id 长度一致，事实上文章段落长度不一。

用户输入问句，判断这句话和知识库是否有关。

这是个 NLP 分类问题。

输入：豆哥群聊所有句子，知识库使用 openmmlab 相关 repo

输出：不同阈值、不同 chunksize 下的 F1 score 曲线

* GT 来自人工标注，评价标准：是否和 openmmlab repo 沾边（开集）
* 知识库不做人工清洗/筛选，直接取 repo 里的 markdown/txt/pdf/word 文件

**第一个问题，** 对 RAG 来说，chunksize 选多大合适？

chunksize 上限为 1500，经验下限为 384

受 splitter 影响，并非选择了 chunksize=512，最终就会变成 512；数值 >= 模型 max_input_size 即可。
无论哪种 splitter 方法，过小的 chunk_size 会导致精度下降。

* encoder max_input_size 是  512，所以有效的测试范围在 128～512 之间
* 调整代码，把 splitter 改成简单的 text_splitter，overlap=0
* 测试不同 chunk_size 下 rejection 精度差异 

注意：为了使每段具有完整语义，实际使用的是 markdown splitter 和 text splitter 混合。

TODO: 增加 3D 绘制。无论何种 splitter，最坏情况下，过小的 chunk_size 会导致 F1 score 下降 10%

**第二个问题，** 应该选择哪种 splitter？

固定 chunk_size=768, overlap=0

* CharacterTextSplitter，用 `\n\n`切分 markdown 文件

    2024-06-17 18:04:44.310 | INFO     | huixiangdou.service.feature_store:analyze:333 - document text histgram count 1150, avg 5063.45, median 2925
    0-7716  79.83%
    7716-15432  14.00%
    15432-23148  4.09%
    23148-30864  0.70%
    30864-38580  0.35%
    38580-46296  0.35%
    46296-54012  0.17%
    54012-61728  0.09%
    61728-69444  0.26%
    69444-77160  0.09%
    77160-84876  0.09%

    2024-06-17 18:04:44.311 | INFO     | huixiangdou.service.feature_store:analyze:334 - document token histgram count 1150, avg 2026.12, median 1085
    0-3245  81.91%
    3245-6490  12.35%
    6490-9735  3.39%
    9735-12980  1.22%
    12980-16225  0.26%
    16225-19470  0.00%
    19470-22715  0.43%
    22715-25960  0.09%
    25960-29205  0.17%
    29205-32450  0.09%
    32450-35695  0.09%

* RecursiveCharacterTextSplitter，分割符有多个，依次尝试 ["\n\n", "\n", " ", ""]

    2024-06-17 18:16:09.360 | INFO     | huixiangdou.service.feature_store:analyze:333 - document text histgram count 9234, avg 629.5, median 708
    0-76  1.83%
    76-152  2.35%
    152-228  1.94%
    228-304  1.75%
    304-380  2.43%
    380-456  4.65%
    456-532  6.06%
    532-608  6.88%
    608-684  13.43%
    684-760  46.19%
    760-836  12.50%

    2024-06-17 18:16:09.364 | INFO     | huixiangdou.service.feature_store:analyze:334 - document token histgram count 9234, avg 254.08, median 261
    0-56  3.97%
    56-112  6.05%
    112-168  7.07%
    168-224  17.24%
    224-280  23.49%
    280-336  19.56%
    336-392  17.63%
    392-448  4.31%
    448-504  0.55%
    504-560  0.11%
    560-616  0.01%

* ChineseRecursiveTextSplitter，考虑中文习惯，把文章切成完整句子。

    2024-06-17 18:29:17.903 | INFO     | huixiangdou.service.feature_store:ingress_reject:388 - documents counter 9212
    Token indices sequence length is longer than the specified maximum sequence length for this model (8979 > 512). Running this sequence through the model will result in indexing errors
    2024-06-17 18:29:21.080 | INFO     | huixiangdou.service.feature_store:analyze:336 - document text histgram count 9212, avg 631.0, median 706
    0-1560  99.97%
    1560-3120  0.00%
    3120-4680  0.02%
    4680-6240  0.00%
    6240-7800  0.00%
    7800-9360  0.00%
    9360-10920  0.00%
    10920-12480  0.00%
    12480-14040  0.00%
    14040-15600  0.00%
    15600-17160  0.01%

    2024-06-17 18:29:21.082 | INFO     | huixiangdou.service.feature_store:analyze:337 - document token histgram count 9212, avg 254.69, median 260
    0-898  99.97%
    898-1796  0.00%
    1796-2694  0.02%
    2694-3592  0.00%
    3592-4490  0.00%
    4490-5388  0.00%
    5388-6286  0.00%
    6286-7184  0.00%
    7184-8082  0.00%
    8082-8980  0.01

* 根据 markdown 格式手写的嵌套 split_md，overlap=32

    2024-06-17 18:42:48.543 | INFO     | huixiangdou.service.feature_store:analyze:336 - document text histgram count 9301, avg 631.1, median 705
    0-1560  99.97%
    1560-3120  0.00%
    3120-4680  0.02%
    4680-6240  0.00%
    6240-7800  0.00%
    7800-9360  0.00%
    9360-10920  0.00%
    10920-12480  0.00%
    12480-14040  0.00%
    14040-15600  0.00%
    15600-17160  0.01%

    2024-06-17 18:42:48.546 | INFO     | huixiangdou.service.feature_store:analyze:337 - document token histgram count 9301, avg 254.83, median 260
    0-897  99.97%
    897-1794  0.00%
    1794-2691  0.02%
    2691-3588  0.00%
    3588-4485  0.00%
    4485-5382  0.00%
    5382-6279  0.00%
    6279-7176  0.00%
    7176-8073  0.00%
    8073-8970  0.00%
    8970-9867  0.01%    

* 手写嵌套，增大参赛量，到 chunk_size 1024

    2024-06-17 20:33:53.003 | INFO     | huixiangdou.service.feature_store:analyze:334 - document text histgram count 6952, avg 842.55, median 960
    0-1559  99.96%
    1559-3118  0.00%
    3118-4677  0.03%
    4677-6236  0.00%
    6236-7795  0.00%
    7795-9354  0.00%
    9354-10913  0.00%
    10913-12472  0.00%
    12472-14031  0.00%
    14031-15590  0.00%
    15590-17149  0.01%

    2024-06-17 20:33:53.005 | INFO     | huixiangdou.service.feature_store:analyze:335 - document token histgram count 6952, avg 339.35, median 348
    0-897  99.96%
    897-1794  0.00%
    1794-2691  0.03%
    2691-3588  0.00%
    3588-4485  0.00%
    4485-5382  0.00%
    5382-6279  0.00%
    6279-7176  0.00%
    7176-8073  0.00%
    8073-8970  0.00%
    8970-9867  0.01%

    持续优化参数：

    2024-06-17 20:44:59.742 | INFO     | huixiangdou.service.feature_store:analyze:334 - document text histgram count 4760, avg 1228.17, median 1425
    0-1560  99.94%
    1560-3120  0.00%
    3120-4680  0.04%
    4680-6240  0.00%
    6240-7800  0.00%
    7800-9360  0.00%
    9360-10920  0.00%
    10920-12480  0.00%
    12480-14040  0.00%
    14040-15600  0.00%
    15600-17160  0.02%

    2024-06-17 20:44:59.744 | INFO     | huixiangdou.service.feature_store:analyze:335 - document token histgram count 4760, avg 493.43, median 510
    0-898  99.75%
    898-1796  0.19%
    1796-2694  0.04%
    2694-3592  0.00%
    3592-4490  0.00%
    4490-5388  0.00%
    5388-6286  0.00%
    6286-7184  0.00%
    7184-8082  0.00%
    8082-8980  0.02%

    optimum 应小于 input median token_id 和模型输入一致的地方。 512


不同的 splitter，切分后，token 长度分布如何？

**第三个问题，** 对拒答任务，BCE 还是 FlagEmbedding ?

- 用 bce
- 用 flag

## 不同 splitter/overlap 设置有多大干扰？
切分方法合理即可，不追求极致?
F1 score 0.5% 以内。
TextSplitter 
RecursiveTextSplitter overlap=32 0.7514
ChineseRecursiveTextSplitter overlap=32 0.7549

## RAG

GT 来自

## Intention
用户输入句子和上下文（可能只有句子），判断是否在发问/求助。

## Topic Extraction