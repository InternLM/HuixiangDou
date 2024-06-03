import os
import pdb
import re
from loguru import logger

def compare_filename(name: str):
    num = name.split('_')[-1]
    if len(num) < 1:
        return name
    num = num.split('.')[0]
    if re.match(r'^\d+$', num):
        return int(num)
    return num


def list_merge(base_dir: str, out_dir: str):

    if not os.path.exists(out_dir):
        os.mkdirs(out_dir)

    dirs = os.listdir(base_dir)

    for dirname in dirs:
        dirpath = os.path.join(base_dir, dirname)
        outfilepath = os.path.join(out_dir, dirname.replace(' ', '')) + '.txt'
        if not os.path.isdir(dirpath):
            continue
        logger.debug(dirpath)
        
        files = os.listdir(dirpath)
        files = list(filter(lambda x: not x.startswith('.') and x.endswith('.txt'), files))
        files = sorted(files, key=compare_filename)

        contents = []
        for filename in files:
            filepath = os.path.join(dirpath, filename)
            with open(filepath) as f:
                contents.append(f.read().strip())
        
        content = '\n'.join(contents)
        # pdb.set_trace()

        with open(outfilepath, 'w') as f:
            f.write(content)

if __name__ == "__main__":
    list_merge('/home/huixiangdou/repodir', '/home/huixiangdou/output')
