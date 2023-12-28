import requests
from readability import Document
from bs4 import BeautifulSoup as BS
import pdb
import requests
import json
import os
import time
import random
import pytoml
from loguru import logger
import argparse

class WebSearch:
    def __init__(self, config_path: dict, retry: int = 3) -> None:
        self.config_path = config_path
        self.retry = retry

    def load_urls(self):
        try:
            with open(self.config_path) as f:
                config = pytoml.load(f)
                return config['web_search']['url_partial_order']
        except Exception as e:
            logger.error(str(e))
        return []

    def load_key(self):
        with open(self.config_path) as f:
            config = pytoml.load(f)
            api_key = config['web_search']['X-API-KEY']
            if api_key is not None and len(api_key) > 0 and api_key != 'YOUR-API-KEY':
                return api_key
        raise Exception('web_search X-API-KEY not found, please input your API key')

    def load_save_dir(self):
        try:
            with open(self.config_path) as f:
                config = pytoml.load(f)
                return config['web_search']['save_dir']
        except Exception:
            pass
        return None

    def google(self, query: str, max_article):
        url = "https://google.serper.dev/search"

        payload = json.dumps({"q": "{}".format(query), "hl": "zh-cn"})
        headers = {'X-API-KEY': self.load_key(), 'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        jsonobj = json.loads(response.text)

        # 带偏序的 url 连接拾取
        keys = self.load_urls()
        urls = dict()

        for organic in jsonobj['organic']:
            link = ''
            print(organic)

            if 'link' in organic:
                link = organic['link']
            else:
                link = organic['sitelinks'][0]['link']

            for key in keys:
                if key in link:
                    if key not in urls:
                        urls[key] = [link]
                    else:
                        urls[key].append(link)
                    break

        logger.debug(f'gather urls: {urls}')

        links = []
        for key in keys:
            if key in urls:
                links += urls[key]

        target_links = links[0:max_article]

        logger.debug(f'target_links:{target_links}')

        articles = []
        for target_link in target_links:
            # network with exponential backoff
            life = 0
            while life < self.retry:
                try:
                    logger.info(f'extract: {target_link}')
                    response = requests.get(target_link)
                    if len(response.text) < 1:
                        break

                    doc = Document(response.text)
                    content_html = doc.summary()
                    title = doc.short_title()
                    soup = BS(content_html, 'html.parser')

                    if len(soup.text) < len(query):
                        break
                    article = '{} {}'.format(title, soup.text)
                    article = article.replace('\n\n', '\n')
                    article = article.replace('\n\n', '\n')
                    article = article.replace('  ', ' ')

                    if len(article) > len(query):
                        articles.append(article)
                    break
                except Exception as e:
                    logger.error(('web_parse exception', query, e, target_link))
                    life += 1

                    randval = random.randint(1, int(pow(2, life)))
                    time.sleep(randval)
        return articles


    def save_search_result(self, query: str, articles: list):
        try:
            save_dir = self.load_save_dir()
            if save_dir is None:
                return
            
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            filepath = os.path.join(save_dir, query)

            text = ''
            if len(articles) > 0:
                text = '\n\n'.join(articles)
            with open(filepath, 'w') as f:
                f.write(text)
        except Exception as e:
            logger.warning(f'error while saving search result {str(e)}')


    def get_with_cache(self, query: str, max_article=1):
        # with exponential rerun
        query = query.strip()

        life = 0
        while life < self.retry:
            try:
                articles = self.google(query=query, max_article=max_article)
                self.save_search_result(query=query, articles=articles)

                return []
            except Exception as e:
                logger.error(('web_search exception', query, str(e)))
                life += 1

                randval = random.randint(1, int(pow(2, life)))
                time.sleep(randval)
        return []


def parse_args():
    parser = argparse.ArgumentParser(description='Web search.')
    parser.add_argument('keywords', type=str, help='Keywords for search and parse.')
    parser.add_argument('--config_path', default='config.ini',
                        help='Feature store configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args

def fetch_web_content(target_link: str):
    response = requests.get(target_link)

    doc = Document(response.text)
    content_html = doc.summary()
    title = doc.short_title()
    soup = BS(content_html, 'html.parser')
    ret = '{} {}'.format(title, soup.text)
    return ret

if __name__ == '__main__':
    parser = parse_args()
    s = WebSearch(config_path = parser.config_path)

    print(s.get_with_cache(args.keywords))
    print(fetch_web_content('https://zhuanlan.zhihu.com/p/359500899'))
