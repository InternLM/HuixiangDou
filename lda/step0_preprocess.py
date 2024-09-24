import jieba
import jieba.posseg as jp
import pdb
import json
import os
from multiprocessing import Process, cpu_count
# https://blog.csdn.net/xyisv/article/details/104482818

pattern = r'[0-9a-f]{40,64}'
def load_stopwords():
    sw = []
    with open('cn_en_stopwords.txt') as f:
        for line in f:
            if len(line.strip()) > 0:
                sw.append(line.strip())
    return sw

def load_documents(n:int = 1):
    basedir = '../repodir.full'
    files = os.listdir(basedir)
    docs = []
    for file in files:
        filepath = os.path.join(basedir, file)
        with open(filepath) as f:
            docs.append((file, filepath))

    length = len(files)
    step = length // n
    remainder = length % n
    
    result = []
    start = 0
    for i in range(n):
        end = start + step + (1 if i < remainder else 0)
        result.append(docs[start:end])
        start = end
    
    return result

def load_newwords():
    words = []
    with open('ner.json', encoding='utf8') as f:
        words = json.load(f)
    return words

def process_data(documents: list, pid: int):
    # add newwords
    new_words = load_newwords()
    for w in new_words:
        jieba.add_word(w)

    stop_words = load_stopwords()
    print('{} start..'.format(pid))
    for filename,filepath in documents:
        d = ''
        with open(filepath) as f:
            d = f.read()
        cuts = [w.word for w in jp.cut(d)]
        
        filtered = []
        for c in cuts:
            c = c.strip()
            if c in stop_words:
                continue

            if 'images' == c:
                continue
            filtered.append(c)
        
        if len(filtered) < 1:
            continue
        new_content = ' '.join(filtered)
        
        with open(os.path.join('preprocess', filename), 'w') as f:
            f.write(new_content)
            f.flush()
    print('{} finish..'.format(pid))

def _get_num_processes():
    num_processes = cpu_count() - 1  # Good habit to leave 1 core.
    return num_processes

def main():
    debug_mode = True

    processes = []
    split_documents = load_documents(n=_get_num_processes())
    for process_id, documents in enumerate(split_documents):
        print(f'Distributing to process[{process_id}]...')

        if debug_mode:
            process_data(documents, process_id)
        else:

            # convert NDArray back to a list, easier.
            process = Process(
                target=process_data,
                args=(
                    documents,
                    process_id,
                ),
            )
            process.start()
            print(f'Distributed to process[{process_id}].')
            processes.append(process)
    for process in processes:
        process.join()

if __name__ == '__main__':
    main()
