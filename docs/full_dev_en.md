# High Precision Configuration

The basic version may not perform well. You can enable these features to enhance performance. The more features you turn on, the better.

1. Use higher accuracy local LLM

   Adjust the `llm.local` model in config.ini to others, seed [opencompass leaderboard](https://rank.opencompass.org.cn/leaderboard-llm).

   This option has a significant effect.

2. Hybrid LLM Service

   For LLM services that support the [openai](https://pypi.org/project/openai/) interface, HuixiangDou can utilize its Long Context ability.
   Using [kimi](https://platform.moonshot.cn/) as an example, below is an example of `config.ini` configuration:

   ```ini
   # config.ini
   [llm]
   enable_local = 1
   enable_remote = 1
   ..
   [llm.server]
   ..
   # open https://platform.moonshot.cn/
   remote_type = "kimi"
   remote_api_key = "YOUR-KIMI-API-KEY"
   remote_llm_max_text_length = 128000
   remote_llm_model = "auto"
   ```

   Note that this feature will increase response time and operating costs.

3. Repo search enhancement

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

4. Tune Parameters

   It is often unavoidable to adjust parameters with respect to business scenarios.

   - Refer to [data.json](./tests/data.json) to add real data, run [test_intention_prompt.py](./tests/test_intention_prompt.py) to get suitable prompts and thresholds, and update them into [worker](./huixiangdou/service/worker.py).
   - Adjust the [number of search results](./huixiangdou/service/worker.py) based on the maximum length supported by the model.
   - Update `web_search.domain_partial_order` in `config.ini` according to your scenarios.
