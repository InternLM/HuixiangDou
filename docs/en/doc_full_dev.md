# High Precision Configuration

The basic version may not perform well. You can enable these features to enhance performance. The more features you turn on, the better.

1. Repo search enhancement

   This feature is suitable for handling difficult questions and requires basic development capabilities to adjust the prompt.

   - Click [sourcegraph-account-access](https://sourcegraph.com/users/tpoisonooo/settings/tokens) to get token

     ```shell
     # open https://github.com/sourcegraph/src-cli#installation
     sudo curl -L https://sourcegraph.com/.api/src-cli/src_linux_amd64 -o /usr/local/bin/src && chmod +x /usr/local/bin/src

     # Enable search and fill the token
     [worker]
     enable_sg_search = 1
     ..
     [sg_search]
     ..
     src_access_token = "${YOUR_ACCESS_TOKEN}"
     ```

   - Edit the name and introduction of the repo, we take opencompass as an example

     ```ini
     # config.ini
     # add your repo here, we just take opencompass and lmdeploy as example
     [sg_search.opencompass]
     github_repo_id = "open-compass/opencompass"
     introduction = "Used for evaluating large language models (LLM) .."
     ```

   - Use `python3 -m huixiangdou.service.sg_search` for unit test, the returned content should include opencompass source code and documentation

     ```shell
     python3 -m huixiangdou.service.sg_search
     ..
     "filepath": "opencompass/datasets/longbench/longbench_trivia_qa.py",
     "content": "from datasets import Dataset..
     ```

   Run `main.py`, HuixiangDou will enable search enhancement when appropriate.

2. Tune Parameters

   It is often unavoidable to adjust parameters with respect to business scenarios.

   - Refer to [data.json](../../tests/data.json) to add real data, run [test_intention_prompt.py](../../tests/test_intention_prompt.py) to get suitable prompts and thresholds, and update them into [prompt.py](../../huixiangdou/service/prompt.py).
   - Adjust the [number of search results](../../huixiangdou/service/serial_pipeline.py) based on the maximum length supported by the model.
   - Update `web_search.domain_partial_order` in `config.ini` according to your scenarios.
