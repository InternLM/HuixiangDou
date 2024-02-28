import json
import math
import os
import re
from datetime import datetime

import loguru
import requests


def get_issue_count(owner, name):
    headers = {
        'Authorization': TOKEN,
    }
    url = f'https://api.github.com/repos/{owner}/{name}/issues'
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        issues = response.json()
        count = issues[0]['number']
    else:
        loguru.logger.error(f'Error fetching issues: {response.status_code}')
        loguru.logger.error(response.text)
        if 'limit' in response.text:
            loguru.logger.error('受到 github 限制，自动结束')
            exit()
        count = 0
    return count


def get_issues_list(owner, name, issue_count):
    headers = {
        'Authorization': TOKEN,
    }
    GITHUB_API_URL = f'https://api.github.com/repos/{owner}/{name}/issues'
    pages = math.ceil(issue_count / 100) + 1
    loguru.logger.info(f'all_pages:{pages}')
    issues_list = []
    for page in range(pages):
        response = requests.get(GITHUB_API_URL,
                                headers=headers,
                                params={
                                    'state': 'all',
                                    'per_page': 100,
                                    'page': {page}
                                })
        if response.status_code == 200:
            issues = response.json()
            for issue in issues:
                if 'issues' in issue['html_url'] and issue['state'] == 'closed':
                    issues_list.append({
                        'number': issue['number'],
                        'title': issue['title'],
                        'html_url': issue['html_url'],
                        'body': issue['body'],
                        'closed_at': issue['closed_at']
                    })
        else:
            loguru.logger.error(
                f'Error fetching issues: {response.status_code}')
            loguru.logger.error(response.text)
    return issues_list


def get_all_comments(owner, name, issue_number):
    headers = {
        'Authorization': TOKEN,
    }
    issue_comments_url = f'https://api.github.com/repos/{owner}/{name}/issues/{issue_number}/comments'
    comments = []
    result_comments = []
    response = requests.get(issue_comments_url, headers=headers)
    if response.status_code != 200:
        loguru.logger.error(
            f'Failed to retrieve comments: {response.status_code} issue_number {issue_number}'
        )
        loguru.logger.error(f'{response.text}')
        if 'limit' in response.text:
            loguru.logger.error('受到 github 限制，自动结束')
            exit()
        return []
    page_comments = response.json()
    if not page_comments:
        return []
    comments.extend(page_comments)
    for i, sub_comment in enumerate(comments):
        comment = {
            'id': i,
            'user': sub_comment['user']['login'],
            'body': sub_comment['body']
        }
        # 删除 comment 引用其他部分，节省空间
        if '> ' in comment['body']:
            quoted_regex = re.compile(r'^>.*(?:\r?\n|\r)?', re.MULTILINE)
            comment['body'] = re.sub(quoted_regex, '', comment['body']).strip()
        result_comments.append(comment)
    return result_comments


def write_all_issues(owener, name, issues_list, max_issue_number):
    # issue number 从大到小获取 comment
    # 单次获取comment可能会有问题，太多了会受到github限制，可能需要多次构建
    for j in range(len(issues_list)):
        issue_number = issues_list[j]['number']
        if issue_number >= max_issue_number:
            continue
        issue_body = issues_list[j]['body']
        issue_comments = get_all_comments(owener, name, issue_number)
        # 保存
        issue_title = issues_list[j]['title']
        forbidden_chars_pattern = r'[<>:"/\\|?*]'  # for windows
        issue_title = re.sub(forbidden_chars_pattern, ' ', issue_title)
        md_basename = f'{issue_number}_{issue_title}.md'
        md_question = issue_body
        md_answer = ''.join([
            f"#### 第{i['id']}条回复来自{i['user']} \n {i['body']} \n"
            for i in issue_comments
        ])
        md_contents = f"""## quesion\n
    =========== question ===========
    {issue_title}\n
    {md_question}
    =========== question ===========\n
    ## answer\n
    =========== answer ===========
    {md_answer}
    =========== answer ===========\n
        """
        with open(os.path.join(EXPORT_DIR, md_basename),
                  mode='w',
                  encoding='utf-8') as file:
            file.write(md_contents)


if __name__ == '__main__':

    # config
    TOKEN = ''
    OWENER = 'InternLM'
    NAME = 'lmdeploy'
    # 每次构建都要把之前构建好的跳过，这里默认一个很大的值
    MAX_ISSUE_NUMBER = 2000
    EXPORT_DIR = './issues'
    SAVE_MONTH = 3  # 保存几个月内的 issue

    # run
    if not os.path.exists(EXPORT_DIR):
        os.mkdir(EXPORT_DIR)
    issues_json_path = os.path.join(EXPORT_DIR, 'git_issues_list.json')
    if not os.path.exists(issues_json_path):
        issue_count = get_issue_count(OWENER, NAME)
        issues_list = get_issues_list(OWENER, NAME, issue_count)
        # clear issues
        current_date = datetime.now()
        for i in issues_list:
            if i['body'] is None:
                issues_list.remove(i)
                continue
            issue_date = datetime.strptime(i['closed_at'][0]['closed_at'],
                                           '%Y-%m-%dT%H:%M:%SZ')
            diff = abs((current_date.year - issue_date.year) * 12 +
                       (current_date.month - issue_date.month))
            if diff > SAVE_MONTH:
                issues_list.remove(i)

        loguru.logger.info(f'create git_issues! {issues_json_path}')
        with open(issues_json_path, 'w') as file:
            json.dump(issues_list, file)
    else:
        loguru.logger.info(f'we already have git_issues! {issues_json_path}')
        with open(issues_json_path, 'r') as file:
            git_all_issues = json.load(file)
            print(git_all_issues)

    write_all_issues(OWENER,
                     NAME,
                     git_all_issues,
                     max_issue_number=MAX_ISSUE_NUMBER)
