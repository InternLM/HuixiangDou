# This is a start-up file for deploying HuixiangDou-WEB on OpenXLab-APPs(https://openxlab.org.cn/apps)
# Some environment variables need to be set before starting up:
# JWT_SECRET=
# REDIS_HOST=
# REDIS_PASSWORD=
# SERVER_PORT=7860 (when deploy on OpenXLab-APPs, this SERVER_PORT should be 7860)

import os

# launch the HuixiangDou-WEB
os.system('python -m web.main')
