# deploy script on OpenXLab-Apps(https://openxlab.org.cn/apps)

import os

# launch the HuixiangDou-WEB
os.system("python -m web.main")

# launch huixiangdou pipeline
os.system("cd web/proxy && python main.py")
