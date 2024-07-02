import json
import os
import re

from loguru import logger

pattern = re.compile(r'^[A-Za-z0-9]+$')

pwd = os.path.dirname(__file__)
query_log = os.path.join(pwd, '..', 'query.log')


def save(_id, sentence):
    if _id not in queries:
        queries[_id] = [sentence]
    else:
        queries[_id].append(sentence)


queries = dict()
with open(query_log) as f:
    query = None

    _id = None
    sentence = ''
    for line in f:
        line = line.strip()
        if len(line) < 5:
            continue

        if line[4] == ' ' and pattern.match(
                line[0:4]) and _id is not None and sentence != '':
            save(_id, sentence)
            _id = line[0:4]
            sentence = line[4:]
        else:
            if line[4] == ' ' and pattern.match(line[0:4]):
                _id = line[0:4]
                sentence = line[4:]
            else:
                sentence += '\n'
                sentence += line

    save(_id, sentence)

counter = 0
for _id in queries:
    with open(os.path.join(pwd, '..', 'queries', _id) + '.txt', 'a') as f:
        values = map(lambda x: x.strip(), queries[_id])
        values = list(set(values))
        counter += len(values)
        json_str = json.dumps(values, ensure_ascii=False)
        f.write(r'{}'.format(json_str))
        f.write('\n')

logger.info(counter)
