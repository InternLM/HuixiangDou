import os

import pytoml


def read_config_ini_files(directory):
    # 遍历指定目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 检查文件扩展名是否为 .ini
            if file == 'config.ini':
                # 构建完整的文件路径
                file_path = os.path.join(root, file)
                try:
                    # 读取并解析 config.ini 文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = pytoml.load(f)
                    print((
                        file_path,
                        config['llm']['server']['remote_llm_max_text_length']))
                    config['llm']['server'][
                        'remote_llm_max_text_length'] = 30000
                    with open(file_path, 'w', encoding='utf8') as f:
                        pytoml.dump(config, f)
                except Exception as e:
                    print(f'An error occurred while reading {file_path}: {e}')


# 指定要遍历的目录
directory_to_crawl = '/root/HuixiangDou/feature_stores'
read_config_ini_files(directory_to_crawl)
