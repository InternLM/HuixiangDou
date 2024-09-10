import os
import shutil

def copy_files(src_dir, dest_dir):
    # 遍历源目录
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            # 构建源文件的完整路径
            src_file = os.path.join(root, file)
            # 构建目标文件的完整路径
            dest_file = os.path.join(dest_dir, file)
            # 复制文件

            shutil.copy(src_file, dest_file)
            print(f"Copied '{src_file}' to '{dest_file}'")

# 指定源目录和目标目录
source_directory = '/home/khj/CNKI_pure_text'
destination_directory = '/home/khj/hxd-ci/repodir'

# 调用函数
copy_files(source_directory, destination_directory)