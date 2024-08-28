import glob
import os

import cv2

# 列出当前目录下的所有png图片
for png_file in glob.glob('*.png'):
    # 读取图片
    img = cv2.imread(png_file)
    # 生成新的文件名
    jpg_file = os.path.splitext(png_file)[0] + '.jpg'
    # 写入jpg图片，设置质量为90
    cv2.imwrite(jpg_file, img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
