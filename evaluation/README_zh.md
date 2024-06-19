# HuixiangDou Evaluation

## Rejection

通过本测试，得到了 text2vec 模型中 chunksize 上下界。

### **1.1 数据说明**

使用的知识库是 openmmlab 相关的 9 个 repo 中的所有 markdown、txt 和 pdf 文档。

累计 1150 个。文档长度均值 5063；长度中位数 2925。

即以下 repo 的文档部分做知识库：

```bash
git clone https://github.com/open-compass/opencompass --depth=1
git clone https://github.com/open-mmlab/mmpose --depth=1
git clone https://github.com/open-mmlab/mmdeploy --depth=1
git clone https://github.com/open-mmlab/mmdetection --depth=1
git clone https://github.com/internlm/lmdeploy --depth=1
git clone https://github.com/internlm/huixiangdou --depth=1
git clone https://github.com/internlm/xtuner  --depth=1
git clone https://github.com/open-mmlab/mmyolo --depth=1
git clone https://github.com/open-mmlab/mmcv --depth=1
```

query 来自 openmmlab 用户群和 ncnn 开发者群，累计 2302 条问题。通过人工标注，判定问题与知识库是否相关。数据见 [正例](https://github.com/tpoisonooo/huixiangdou-evaluation-results/blob/main/rejection/gt_good.txt) 和 [负例](https://github.com/tpoisonooo/huixiangdou-evaluation-results/blob/main/rejection/gt_bad.txt)。

### **1.2 测试方法**

把正反例填进 `gt_bad.txt` 和 `gt_good.txt`。执行：

```
python3 evaluation/rejection/build_fs_and_filter.py
```

这个代码会打开调试模式，统计 tokenize 后的长度。

为了让 token 长度刚好和模型匹配（如 512），自行调整 chunksize 参数。

```
# build_fs_and_filter.py
# 改成希望的长度，如 1240。
calculate(1240)

# 支持多进程测试，提高效率
pool = NestablePool(6)
result = pool.map(calculate, range(128, 512, 32))
pool.close()
pool.join()
print(result)
```

使用 `python3 plot.py` 绘制不同 chunksize 和 throttle 下的 F1。结果样例：

<img src="rejection/plot_example.png" width="400">

### **1.3 测试结论**

对 bce-embedding-base_v1

* chunksize 范围应在 (512, 1500)
* 右值取到的最佳 F1@throttle 为 75.39@0.41
* chunksize 取 640 时，F1 可达到 75.88

对 bge-large-zh-v1.5
* chunksize 范围应在 (423, 1240)
* embedding.tokenzier 的压缩率略低
* 右值取到的最佳 F1@throttle 为 72.23@0.34

splitter 选择依据
* 中文优先 `ChineseTextSplitter`，会出现离心值
* 英文 `langchain.RecursiveTextSplitter`，切中文语料更碎但没有离心值
* `CharacterTextSplitter` 实际没切片作用，避免直接用
