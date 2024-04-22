import json

with open('filter.jsonl', 'w') as fout:
    with open('groups/18356748488@chatroom@reconstruct.txt.llm') as f:
        while True:
            line = f.readline()
            if not line:
                break
            if len(line) < 1:
                continue

            json_obj = json.loads(line)
            text = json_obj['text']
            if 'cr_need' in json_obj and json_obj['cr_need']:
                fout.write(line)
