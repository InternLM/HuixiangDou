# RAG 标注知识问答类训练数据

RAG 标注训练数据是否有用，请参考论文：

- [Reformatted Alignment](https://arxiv.org/abs/2402.12219)
- [CherryLLM](https://arxiv.org/abs/2308.12032)

本文介绍如何使用 HuixiangDou 在脏数据上标注 openmmlab+internlm 知识类问题，使用 10 个 repo（见配置文件）的文档做知识库。

## 一、调整配置文件

基于 [config-alignment-example.json](../config-alignment-example.ini) 做几处修改：

1. 设置 bce 模型路径，执行 `python3 -m huixiangdou.service.feature_store --config_path config-alignment-example.ini`，用自己的知识库提取特征
2. 配置 config 中网络搜索 key
3. 配置 sourcegraph key。可能需要私有化部署一套 sourcegraph
4. 选择使用的 remote LLM 并配置 RPM，一般标注用 GPT。xi-api 是国内的一个代理

## 二、运行

[大佬数据集](../resource/rag_example_input.json) 是一个例子，从 openmmlab 用户问题中筛选包含 “大佬” 二字的 86 句并脱敏。

启动 LLM 代理服务监听 9999 端口

```bash
python3 -m huixiangdou.service.llm_server_hybrid  --config_path config-alignment-example.ini
```

开个新窗口，执行 `rag.py`

```bash
python3 -m huixiangdou.rag --help
# 支持多进程
..
python3 -m huixiangdou.rag --config_path config-alignment-example.ini
```

结果默认保存到 `resource` 目录，每个进程保存 1 个文件。

## 三、结果分析

[大佬结果](../resource/rag_example_output.json) 是真实运行的结果。

由于数据挺脏，所以并非所有 prompt 都应该处理。例如

```bash
  {
    "id": 0,
    "query": "这种，看着就大佬味道",
    "direct_reply": "",
    "rag_reply": "",
    "code": 1,
    "reason": "query is not a question",
    "refs": []
  }
```

- code 是错误码，所有错误见 service/helper.py
- direct_reply 是 LLM 原本回复，当 code 为 0 时才调用
- reason 是错误的原因
- refs 是参考文档

下面是个示例，`rag_reply` 更具体，不会像原始的 `direct_reply` 更“务虚”。可以进入下一阶段清洗流程。

```bash
{
  "id": 3,
  "query": "有大佬用onnx 的fp 16模型转TNN嘛",
  "direct_reply": "ONNX（Open Neural Network Exchange）是一个开放格式，用于表示深度学习模型，允许AI开发人员在不同的框架和工具之间轻松转换模型。FP16指的是16位浮点数精度，这是深度学习中常用的一种数值精度格式，它有助于减少模型的大小和计算资源的需求。\n\nTNN（Tencent Neural Network）是腾讯开源的一个轻量级、高性能的深度学习推理引擎。TNN支持多种模型格式，包括ONNX。\n\n将ONNX的FP16模型转换为TNN支持的格式，通常需要以下步骤：\n\n1. **模型转换**：首先，你需要将ONNX模型转换为TNN支持的格式。TNN可能直接支持ONNX模型，但为了确保最佳性能和兼容性，你可能需要使用TNN提供的工具将ONNX模型转换为TNN的特定格式。\n\n2. **精度调整**：由于你提到的是FP16模型，你需要确保TNN支持FP16精度。如果TNN原生不支持FP16，你可能需要在转换过程中将模型的精度从FP16转换为TNN支持的精度格式，比如FP32。\n\n3. **优化**：转换后，你可能需要对模型进行优化以适应TNN的推理引擎。这可能包括内存优化、计算图优化等。\n\n4. **测试**：在转换和优化之后，你应该对模型进行测试，确保它在TNN上运行时保持原有的性能和准确性。\n\n请注意，具体的转换和优化步骤可能会根据TNN的版本和具体功能有所不同。建议查看TNN的官方文档和社区资源，以获取最新和最准确的信息。如果你在转换过程中遇到任何问题，你也可以在相关的开发者社区或论坛中寻求帮助。",
  ..
  "rag_reply": "根据提供的材料，如果你想要将ONNX的FP16模型转换为TNN（腾讯神经网络）模型，你需要关注几个关键点：\n\n1. **模型转换工具**：材料中提到了`tools/deploy.py`这个工具，它被用来将模型转换为不同的后端格式。虽然在材料中没有直接提到TNN，但是你可以参考这个工具的使用方式来转换模型。\n\n2. **模型格式兼容性**：材料中列出了多个支持的后端，包括ONNX Runtime、TensorRT、ncnn、PPLNN、OpenVINO等，但没有提到TNN。因此，可能需要使用其他工具或方法来完成转换。\n\n3. **FP16支持**：材料中提到了FP16精度的模型转换，这意味着原始模型可能支持FP16格式。在转换到TNN时，你需要确保目标平台也支持FP16，以便能够利用这一精度优势。\n\n4. **社区和文档**：由于材料中没有直接提到TNN，你可能需要查阅TNN的官方文档或社区讨论，看看是否有人已经实现了类似的转换，或者是否有官方的指导和工具可以使用。\n\n5. **自定义转换**：如果现有的工具和方法不能满足你的需求，你可能需要自己实现一个转换流程。这可能包括将ONNX模型转换为TNN支持的中间格式，然后再转换到TNN的最终格式。\n\n总的来说，虽然材料中没有直接提供将ONNX FP16模型转换为TNN模型的指导，但你可以参考已有的模型转换工具和方法，同时查阅TNN相关的资源来完成这一任务。如果需要，也可以考虑自定义转换流程。",
  "code": 0,
  "reason": "success",
  "refs": [
    "mmocr.md",
    "deploy.md",
    "mmrotate.md",
    "mmpose.md",
    "mmdet.md",
    "model_convert.md",
    "mmseg.md"
  ]
}
```
