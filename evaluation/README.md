# HuixiangDou Evaluation

## Rejection

Based on this test, the upper and lower bounds of the chunksize in the text2vec model were obtained.

### **1.1 Data Description**

The knowledge base used consists of all markdown, txt, and pdf documents from 9 repositories related to openmmlab.

A total of 1150 documents were accumulated. The mean document length is 5063; the median length is 2925.

That is, the document parts of the following repositories were used as the knowledge base:

```bash
git clone https://github.com/open-compass/opencompass  --depth=1
git clone https://github.com/open-mmlab/mmpose  --depth=1
git clone https://github.com/open-mmlab/mmdeploy  --depth=1
git clone https://github.com/open-mmlab/mmdetection  --depth=1
git clone https://github.com/internlm/lmdeploy  --depth=1
git clone https://github.com/internlm/huixiangdou  --depth=1
git clone https://github.com/internlm/xtuner   --depth=1
git clone https://github.com/open-mmlab/mmyolo  --depth=1
git clone https://github.com/open-mmlab/mmcv  --depth=1
```

The queries come from the openmmlab user community and the ncnn developer community, with a total of 2302 questions. Under manual annotation, it was determined whether the questions are relevant to the knowledge base. The data can be seen in [Positive Examples](https://github.com/tpoisonooo/huixiangdou-evaluation-results/blob/main/rejection/gt_good.txt) and [Negative Examples](https://github.com/tpoisonooo/huixiangdou-evaluation-results/blob/main/rejection/gt_bad.txt).

### **1.2 Test Method**

Fill the positive and negative examples into `gt_bad.txt` and `gt_good.txt`. Execute:

```
python3 evaluation/rejection/build_fs_and_filter.py
```

This script will open debug mode and count the length after tokenization.

To match the token length exactly with the model (e.g., 512), adjust the chunksize parameter yourself.

```
# build_fs_and_filter.py
# Change to the desired length, such as 1240.
calculate(1240)

# Supports multi-process testing to improve efficiency
pool = NestablePool(6)
result = pool.map(calculate, range(128, 512, 32))
pool.close()
pool.join()
print(result)
```

Use `python3 plot.py` to plot the F1 under different chunksizes and throttles. An example of the results is shown below:

<img src="rejection/plot_example.png" width="600">

### **1.3 Test Conclusion**

For bce-embedding-base_v1

- The chunksize range should be (512, 1500)
- The best F1@throttle obtained on the right value is 75.39@0.41
- When chunksize is taken as 640, F1 can reach 75.88

For bge-large-zh-v1.5

- The chunksize range should be (423, 1240)
- The compression rate of embedding.tokenzier is slightly lower
- The best F1@throttle obtained on the right value is 72.23@0.34

The basis for choosing splitter is:

- Chinese priority `ChineseTextSplitter`, which will result in centrifugal values
- English `langchain.RecursiveTextSplitter`, which cuts Chinese corpus more finely but does not have centrifugal values
- `CharacterTextSplitter` does not actually slice and should be avoided for direct use

### **1.4 Comparison of Approaches**

We also compared other methods and models:

|    Approach    | F1 score |                                                                                                     Description                                                                                                      |
| :------------: | :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|      Ours      |  75.88   | Tested using [bce-embedding-base_v1](https://github.com/netease-youdao/BCEmbedding) in conjunction with a specific splitter. Note that inappropriate splitter and distance_strategy can severely affect the accuracy |
| bge-v1.5-large |  72.23   |                                                                     Tested using [bge-large-zh-v1.5](https://github.com/FlagOpen/FlagEmbedding)                                                                      |
|     bge-m3     |  70.62   |   Tested using [m3](https://github.com/FlagOpen/FlagEmbedding) for dense retrieval. Note that m3 has a maximum input token length of 8192, and the test data cannot fully utilize the model's encoding capability    |
| hybrid search  |  63.85   |                       Tested [m3](https://github.com/FlagOpen/FlagEmbedding) dense + sparse retrieval rejection effects based on [milvus WeightedRanker](https://github.com/milvus-io/milvus)                        |
