import json
import os

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_3d():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for jsonl_file in os.listdir('./'):

        if not jsonl_file.endswith('.jsonl'):
            continue

        if not 'chunk_size' in jsonl_file:
            continue

        x = []
        y = []
        z = []
        print(jsonl_file)

        datas = []
        with open(jsonl_file) as f:
            for json_str in f:
                json_obj = json.loads(json_str)
                datas.append(json_obj)

        datas.sort(key=lambda x: x['throttle'])

        for data in datas:
            chunk_size = data['chunk_size']
            throttle = data['throttle']
            f1 = data['f1']

            x.append(chunk_size)
            y.append(throttle)
            z.append(f1)

        # 绘制3D曲线
        ax.plot(x, y, z)

    # 添加标题和标签
    ax.set_title('3D Line Plot')
    ax.set_xlabel('chunk_size')
    ax.set_ylabel('throttle')
    ax.set_zlabel('f1')

    # 显示图形
    plt.show()


def plot_cross_splitter():
    fig = plt.figure()
    for splitter in os.listdir('./'):

        if not splitter.startswith('chunk_size'):
            continue

        if not os.path.isdir(splitter):
            continue

        items = []
        for jsonl_file in os.listdir(splitter):
            if not 'chunk_size' in jsonl_file:
                continue

            print(splitter, jsonl_file)
            datas = []

            with open(os.path.join(splitter, jsonl_file)) as f:
                for json_str in f:
                    json_obj = json.loads(json_str)
                    datas.append(json_obj)
            datas.sort(key=lambda x: x['f1'])

            items.append({
                'chunk_size': datas[-1]['chunk_size'],
                'f1': datas[-1]['f1']
            })

        items.sort(key=lambda x: x['chunk_size'])
        x = []
        y = []
        for item in items:
            if item['chunk_size'] > 1000:
                continue
            x.append(item['chunk_size'])
            y.append(item['f1'])
        print(x, y)
        # 绘制曲线
        label_name = splitter.split('chunk_size_')[-1]
        plt.plot(x, y, label=label_name)

    # 添加标题和标签
    plt.xlabel('chunk_size')
    plt.ylabel('best_f1')
    plt.legend()
    # 显示图形
    plt.show()


if __name__ == '__main__':
    plot_3d()
