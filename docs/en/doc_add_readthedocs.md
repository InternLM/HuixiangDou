# Adding `chat_with_repo` to readthedocs for Free

This article introduces how to implement `chat_with_repo` on Read the Docs at zero cost. See [HuixiangDou Read the Docs documentation](https://huixiangdou.readthedocs.io).

The deployment workflow is as follows:

<img src="https://github.com/user-attachments/assets/d15935fa-a8fa-49ed-9995-7549ab1f71dc"  width="400">

Where:
* [Read the Docs](https://readthedocs.io) hosts Chinese and English documents
* [OpenXLab](https://openxlab.org.cn/apps) provides an HTTPS entrance (Read the Docs cannot embed HTTP) and CPU
* [SiliconCloud](https://siliconflow.cn/siliconcloud) provides text2vec, reranker, and LLM model APIs

We need to use readthedocs custom theme, adding a button to the theme.

1. When the button is clicked, create an `iframe` to load the HTTPS version of Huixiang Dou's Gradio UI
2. HTTPS requires domain name verification. You can use the random subdomain provided by OpenXLab
3. The GPU resources in OpenXLab are limited, so we use the free model APIs provided by SiliconCloud

Here are the steps to follow.

## I. Prepare Code and Documentation

Assuming you use all the documents of `mmpose` as the knowledge base, put the knowledge base into repodir

```bash
cd HuixiangDou
mkdir repodir
git clone https://github.com/open-mmlab/mmpose  --depth=1
# Remove the .git of the knowledge base
rm -rf .git
```

Adjust the default configuration of `gradio_ui.py` to use `config-cpu.ini`
```bash
# huixiangdou/gradio_ui.py
    parser.add_argument(
        '--config_path',
        default='config-cpu.ini',
        type=str,
..
```

Commit the knowledge base and the Huixiangou project to Github together, for example, the `for-openxlab-readthedocs` branch of [huixiangdou-readthedocs](https://github.com/tpoisonooo/huixiangdou-readthedocs/tree/for-openxlab-readthedocs).

## II. Create an OpenXLab Application

Open [OpenXLab](https://openxlab.org.cn/apps) and create a `Gradio` type application.

1. Enter the Github address and branch name from the previous step
2. Choose the CPU server

After confirmation, modify the application settings:

* Add `huixiangdou/gradio_ui.py` to `Customize Startup File` 
* Since the code is open source, you need to configure environment variables. HuixiangDou prioritizes using the token in the `config-cpu.ini`. If it cannot be found, it will try to check `SILICONCLOUD_TOKEN` and `LLM_API_TOKEN`, as shown in the figure:

    <img src="https://github.com/user-attachments/assets/66291c65-1a5e-495a-aad6-e8962bef6bb6"  width="400">

Start the application. The first run takes about **10 minutes** to build the feature library. After it's done, you should see a gradio application. For example:

```bash
https://openxlab.org.cn/apps/detail/tpoisonooo/HuixiangDou-readthedocs 
```

Press F12 in the browser to check the source code and obtain the corresponding HTTPS address for this service:

```JavaScript
src="https://g-app-center-000704-0786-wrbqzpv.openxlab.space" 
```

As long as the application data is not deleted, this address is **fixed**.

## III. Use Read the Docs Custom Theme

Assuming you are already familiar with the basic usage of Read the Docs, you can directly copy the HuixiangDou docs directory

* zh or en directory
* requirements/doc.txt sets the custom theme

[Here](https://github.com/tpoisonooo/pytorch_sphinx_theme/) is the implementation of our custom theme, mainly:

1. Create a `chatButton` and an empty container in [layout.html](https://github.com/tpoisonooo/pytorch_sphinx_theme/blob/3db120b0f1e064425f37e98368dcea49972702e9/pytorch_sphinx_theme/layout.html#L324)
2. Bind an event to `chatButton`. When the button is clicked, the empty container loads the HTTPS address, for example, the previous one:

    ```bash
    https://g-app-center-000704-0786-wrbqzpv.openxlab.space 
    ```

    You can modify your preferred style in [theme.css](https://github.com/tpoisonooo/pytorch_sphinx_theme/blob/master/pytorch_sphinx_theme/static/css/theme.css).

Finally, configure your project on readthedocs.io, and `Build Version` will do.
