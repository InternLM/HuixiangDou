import requests
import math
import re
import os
import pickle

TOKEN = ''
OWENER = 'InternLM'
NAME = 'lmdeploy'
export_dir = './issues'

headers = {
    'Authorization': TOKEN,
}

def get_issue_count(owner, name):
    url = f"https://api.github.com/repos/{owner}/{name}/issues"
    response = requests.get(url=url,headers=headers)
    if response.status_code == 200:
        issues = response.json()
        count = issues[0]['number']
    else:
        print(f"Error fetching issues: {response.status_code}")
        print(response.text)
        count = 0
    return count

def get_issues_list(owner,name,issue_count):
    GITHUB_API_URL = f"https://api.github.com/repos/{owner}/{name}/issues"
    pages = math.ceil(issue_count/100) +1 
    print("all_pages:",pages)
    issues_list = []
    for page in range(pages):
        response = requests.get(GITHUB_API_URL, headers=headers,params={'state': 'all','per_page':100,'page':{page}})
        if response.status_code == 200:
            # 解析JSON响应体为Python对象
            issues = response.json()
            for issue in issues:
                if "issues" in issue['html_url'] and issue['state']=='closed':
                    issues_list.append({'number':issue['number'],'title':issue['title'],'html_url':issue['html_url'],'body':issue['body'],'closed_at':issue['closed_at']})
        else:
            print(f"Error fetching issues: {response.status_code}")
            print(response.text)
    return issues_list

def get_all_comments(owner,name,issue_number):
    issue_comments_url = f'https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/comments'
    comments = []
    result_comments = []
    response = requests.get(issue_comments_url,headers=headers)
    if response.status_code != 200:
        print('Failed to retrieve comments:', response.status_code,"issue_number",issue_number)
        return []
    page_comments = response.json()
    if not page_comments:  
        print("no comment")
        return []
    comments.extend(page_comments)
    for i,sub_comment in enumerate(comments) :
        comment = {'id':i,'user':sub_comment['user']['login'],'body':sub_comment['body']}
        # 删除 comment 引用其他部分，节省空间
        if '> ' in comment['body']:
            quoted_regex = re.compile(r'^>.*(?:\r?\n|\r)?', re.MULTILINE)
            comment['body'] = re.sub(quoted_regex, '', comment['body']).strip()
        result_comments.append(comment)
    return result_comments

def write_all_issues(issues_list):
    # issue number 从大到小获取 comment
    # 单次获取comment可能会有问题，太多了会受到github限制，可能需要多次构建
    MAX_NUMBER = 1000 # 每次构建都要把之前构建好的跳过，这里默认一个很大的值
    for j in range(len(issues_list)):
        issue_number = issues_list[j]['number']
        if issue_number >= MAX_NUMBER:
            print("跳过了",issue_number)
            continue
        issue_body = issues_list[j]['body']
        issue_comments = get_all_comments(OWENER,NAME,issue_number)
        # 保存
        issue_title = issues_list[j]['title']
        forbidden_chars_pattern = r'[<>:"/\\|?*]' # for windows
        issue_title = re.sub(forbidden_chars_pattern, ' ', issue_title)
        md_basename = f"{issue_number}_{issue_title}.md"
        md_question = issue_body
        md_answer = ''.join([f"#### 第{i['id']}条回复来自{i['user']} \n {i['body']} \n"  for i in issue_comments])
        md_contents = f"""## quesion\n
    =========== question ===========
    {md_question}
    =========== question ===========\n
    ## answer\n
    =========== answer ===========
    {md_answer}
    =========== answer ===========\n
        """
        with open(os.path.join(export_dir,md_basename),mode='w',encoding='utf-8') as file:
            file.write(md_contents)

# get issues list
issue_count = get_issue_count(OWENER,NAME)
issues_list = get_issues_list(OWENER,NAME,issue_count)

# 不需要每次都全量获取，先存储本地变量再读取comment
with open('github_all_issues.pkl', 'wb') as file:
    pickle.dump(issues_list, file)

with open('github_all_issues.pkl', 'rb') as file:
    git_all_issues = pickle.load(file)

# 过滤空issue
for i in git_all_issues:
    if i['body'] is None:
        git_all_issues.remove(i)