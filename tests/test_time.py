import time
from datetime import datetime

current_time = time.time()  # 获取当前时间戳
dt_object = datetime.fromtimestamp(current_time)  # 将时间戳转换为datetime对象

# 获取当天自午夜以来的总分钟数
total_minutes_since_midnight = dt_object.hour * 60 + dt_object.minute

print(total_minutes_since_midnight)
