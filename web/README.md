# web

## environment

```shell
# set your service endpoint(open to Internet callback from lark and wechat)
export HUIXIANGDOU_MESSAGE_ENDPOINT=http://ip:port
```

## 启动服务

1. 设置环境变量，启动 redis-server。必须

```bash
$ cat env.sh

export PYTHONUNBUFFERED=1
export REDIS_HOST=10.1.52.22
export REDIS_PASSWORD=${REDIS_PASSWORD}
export REDIS_PORT=6380
export JWT_SECRET=${JWT_SEC}
export SERVER_PORT=7860
export HUIXIANGDOU_LARK_ENCRYPT_KEY=thisiskey
export HUIXIANGDOU_LARK_VERIFY_TOKEN=sMzyjKi9vMlEhKCZOVtBMhhl8x23z0AG
export HUIXIANGDOU_MESSAGE_ENDPOINT=http://10.1.52.36:18443
export COOKIE_SECURE=1
```

2. 编译&运行前后端

```bash
cd front-end
npm install && npm run build

如果 `node -v` 版本老 （10.x），这么升级 node 版本
sudo npm install n -g
sudo n stable
hash -r
node -v
v20.12.0
```

运行

```bash
python3 -m web.main
```

如何不用 https 安全链接，需要 `unset COOKIE_SECURE`

4. 运行算法侧

```bash
先开个窗口，启动 LLM
python3 -m huixiangdou.service.llm_server_hybrid --config_path config-template.ini

再开个窗口，监听服务
python3 -m web.proxy.main
```

5. 测试
打开服务器 7860 端口，创建知识库测试效果