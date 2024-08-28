# SFT data scripts and training configs

> \[!NOTE\]
>
> <div align="center">
> This part is not for beginner, please know about <a href="https://github.com/huggingface/transformers/">transformers</a>, <a href="https://arxiv.org/abs/2203.15556">scaling law</a> and <a href="https://github.com/OpenAccess-AI-Collective/axolotl">SFT</a> first. Basic computer network and python programming knowledge also required.
> </div>

Here is directory description:

|             script             |                              desc                              |
| :----------------------------: | :------------------------------------------------------------: |
|  reconstruct_wechat_group.py   |               reconstruct wechat group messages                |
| reconstruct_filter_annotate.py | filter data with puyu+kimi, manually annotate, manually review |
|    reconstruct_check_llm.py    |                   recheck 14B & 32B results                    |
|      convert_to_alpaca.py      |            convert raw group data to alpaca format             |

# Reproduce HuixiangDou-CR

## 1. Prepare Data

- Get all WeChat group chats, use `python3 reconstruct_wechat_group.py` to split it and filter with LLM

- `python3 reconstruct_filter_annotate.py` to filter, annotate and manually check

  Now you can get [gt.jsonl](https://huggingface.co/datasets/tpoisonooo/HuixiangDou-CR/blob/main/gt.jsonl)

- Convert `gt.jsonl` to alpaca format, use `convert_to_alpaca.py`

  Finally we have [alpaca.json](https://huggingface.co/datasets/tpoisonooo/HuixiangDou-CR/blob/main/alpaca.json) for SFT

## 2. Train

Install [axolotl](https://github.com/OpenAccess-AI-Collective/axolotl), update your model path and data path in [axolotl_configs](./axolotl_configs/).

Let's take [qwen2-lora-0.5B.yaml](./axolotl_configs/qwen2-lora-0.5B.yaml) as example.

```bash
# config paths
base_model: /workspace/models/Qwen1.5-0.5B-Chat
..
datasets:
  - path: /workspace/axolotl/alpaca.json
    type: alpaca
    ..
output_dir: ./out-qwen0.5
```

Train the model

```bash
accelerate launch -m axolotl.cli.train examples/qwen/qwen2-lora-0.5B.yaml
```

Fine-tuned LoRA weights can be found in [huggingface](https://huggingface.co/tpoisonooo).

Merge LoRA weights

```bash
python3 -m axolotl.cli.merge_lora examples/qwen/qwen2-lora-0.5B.yaml
```

## 3. Validate

Serving merged Qwen model as `openai` API with [vLLM](https://github.com/vllm-project/vllm)

```bash
python -m vllm.entrypoints.openai.api_server --served-model-name LoRA-Qwen1.5-0.5B-Chat --model /workspace/axolotl/out-qwen0.5/merged/ --port 29999 --max-model-len 8192
```

Evaluate the precision and F1 score, **use your own IP and port** in the python code.

```bash
python3 reconstruct_filter_annotate.py --action metric --llm-type Qwen1.5-0.5B-Chat
```
