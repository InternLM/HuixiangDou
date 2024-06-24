import re
import os
import json
pattern = re.compile(r'^[A-Za-z0-9]+$')


def save(_id, sentence):
    with open(os.path.join('/workspace/queries', _id) + '.txt', 'a') as f:
        # json_str = json.dumps({'data': sentence}, ensure_ascii=False)
        # f.write(r'{}'.format(json_str))
        f.write(r'{}'.format(sentence))
        f.write('\n')

with open('/workspace/query.log') as f:
    query = None

    _id = None
    sentence = ''
    for line in f:
        line = line.strip()
        if len(line) < 5:
            continue

        if line[4] == ' ' and pattern.match(line[0:4]) and _id is not None and sentence != '':
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
