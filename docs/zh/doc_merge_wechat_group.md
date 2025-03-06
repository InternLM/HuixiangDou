# 在多个微信群中转发消息

我们使用[商业版 wkteam](http://121.229.29.88:6327) 转发多个微信群的消息。
目前支持：
- 普通文本
- 引用类消息
- 图片
- 链接
- 命令机器人撤回

<img src="https://github.com/user-attachments/assets/9d8fd881-9477-47ec-b1b9-dd2d6935882f" width="600">

## 部署说明

如果仅想转发消息，**不需要 GPU**、**不需要 redis**、**需要公网 ip**

1. 打开 [wkteam](http://121.229.29.88:6327) 注册试用版

2. 填写 [config.ini](../../config.ini) 中的 `frontend.wechat_wkteam` 部分

    例如：
   
    ```text
    [frontend.wechat_wkteam]
    account = "wkteam手机号"
    password = "wkteam密码"
    proxy = 3  # 上海地区
    dir = "wkteam"
    callback_ip = "你的公网 IP" 
    callback_port = 9528

    # !!! `proxy` is very import parameter, it's your account location
    # 1：北京 2：天津 3：上海 4：重庆 5：河北
    # 6：山西 7：江苏 8：浙江 9：安徽 10：福建
    # 11：江西 12：山东 13：河南 14：湖北 15：湖南
    # 16：广东 17：海南 18：四川 20：陕西
    # bad proxy would cause account deactivation !!!
    ```

4. 运行 `wechat.py`，微信扫描二维码登录，然后注册 callback 地址。

   ```text
   python3 huixiangdou/frontend/wechat.py --login --forward
   ```

   若运行成功，会看到以下日志，同时 `wkteam/license.json` 会记录完整的账号信息。

    ```bash
    # 设置 callback 地址日志
    .. set callback url http://xxx/callback
    .. {"code":"1000","message":"设置成功","data":null}
    .. login success, all license saved to wkteam/license.json
    
    # 保存账号信息
    cat wkteam/license.json
    {
    "auth": "xxx",
    "wId": "xxx",
    "wcId": "wxid_xxx",
    "qrCodeUrl": "http://wxapii.oosxxx"
    }
    ```

5. 获取 GroupID。在你想要转发的群里发条消息，查看日志或 `wkteam/wechat_message.jsonl` 里的 GroupID 字段。填入 `config.ini`，例如：

    ```text
    [frontend.wechat_wkteam.43925126702]
    name = "茴香豆群（大暑）"
    introduction = "github https://github.com/InternLM/HuixiangDou 用户体验群"
    ```

6. 重新运行脚本
    ```text
    python3 huixiangdou/frontend/wechat.py --login --forward
    ```
