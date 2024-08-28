# 在 readthedocs 实现 `chat_with_repo`

本文介绍如何零成本在 readthedocs 实现 `chat_with_repo`。效果见 [HuixiangDou readthedocs 文档](https://huixiangdou.readthedocs.io)。

部署图如下：

<img src="https://github.com/user-attachments/assets/d15935fa-a8fa-49ed-9995-7549ab1f71dc" width="400">

其中：
* [readthedocs](https://readthedocs.io) 托管中英文文档
* [OpenXLab](https://openxlab.org.cn/apps) 提供 https 入口（readthedocs 无法内嵌 http）和 cpu
* [SiliconCloud](https://siliconflow.cn/siliconcloud) 提供 text2vec、reranker 和 LLM 模型 API

我们需要使用 readthedocs 的自定义 theme，在 theme 中添加按钮。

1. 点击按钮时，创建一个 `iframe` 加载 https 版茴香豆
2. https 需要审核域名。可以用 OpenXLab 提供的随机子域名
3. OpenXLab 中 GPU 资源有限，我们使用 SiliconCloud 提供的免费模型 API

以下是操作步骤。

## 一、准备代码和文档

假设用 mmpose 所有文档做知识库，把知识库放入 repodir

```bash
cd HuixiangDou
mkdir repodir
git clone https://github.com/open-mmlab/mmpose --depth=1
# 移除知识库的 .git
rm -rf .git
```

调整 `gradio_ui.py` 的默认配置，使用 `config-cpu.ini`
```bash
# huixiangdou/gradio_ui.py
    parser.add_argument(
        '--config_path',
        default='config-cpu.ini',
        type=str,
..
```

连同知识库和 Huixiangou 项目，一起提交到 Gtihub，例如 [huixiangdou-readthedocs](https://github.com/tpoisonooo/huixiangdou-readthedocs/tree/for-openxlab-readthedocs) 的 `for-openxlab-readthedocs` 分支。

## 二、创建 OpenXLab 应用

打开 [OpenXLab](https://openxlab.org.cn/apps)，创建 `Gradio` 类型应用。

1. 填入上一步的 Github 地址和分支名称
2. 服务器选择 CPU

确认后，修改应用设置：

* `自定义启动文件` 改为 `huixiangdou/gradio_ui.py`
* 由于代码已开源，需配置环境变量。HuixiangDou 优先使用配置中的 token，找不到时会尝试检查 `SILICONCLOUD_TOKEN` 和 `LLM_API_TOKEN`，如图：

    <img src="https://github.com/user-attachments/assets/66291c65-1a5e-495a-aad6-e8962bef6bb6" width="400">


启动。首次运行需要 **10min 左右**建立特征库，结束后应该能看到一个 gradio 应用。例如:

```bash
https://openxlab.org.cn/apps/detail/tpoisonooo/HuixiangDou-readthedocs
```

在浏览器中按 F12，检查源码，可获得此服务对应的 https 地址：

```JavaScript
src="https://g-app-center-000704-0786-wrbqzpv.openxlab.space"
```

只要不删除应用数据，这个地址是**固定的**。


## 三、使用 readthedocs 自定义主题

假设你已经熟悉 readthedocs 基本用法，可以直接拷贝 HuixiangDou docs 目录

* zh 或 en 目录
* requirements/doc.txt 设置自定义主题

[这里](https://github.com/tpoisonooo/pytorch_sphinx_theme/
) 是我们的自定义主题的实现，主要是：

1. 在 [layout.html](https://github.com/tpoisonooo/pytorch_sphinx_theme/blob/3db120b0f1e064425f37e98368dcea49972702e9/pytorch_sphinx_theme/layout.html#L324) 创建了一个 `chatButton` 和空白 container
2. 为 `chatButton` 绑定事件。按钮点击时，空白 container 加载 https 地址，例如前面的：

    ```bash
    https://g-app-center-000704-0786-wrbqzpv.openxlab.space
    ```

    在 [theme.css](https://github.com/tpoisonooo/pytorch_sphinx_theme/blob/master/pytorch_sphinx_theme/static/css/theme.css) 中，您可修改自己喜欢的样式。

最后，在 readthedocs.io 配置自己的项目，`Build Version` 即可。
