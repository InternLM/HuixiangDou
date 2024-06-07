# Copyright (c) OpenMMLab. All rights reserved.
"""Web search utils."""
import argparse
import json
import os
import types
import time
import asyncio
import pytoml
import requests
from bs4 import BeautifulSoup as BS
from duckduckgo_search import DDGS
from loguru import logger
from readability import Document
import asyncio
import nest_asyncio
from .helper import check_str_useful
import_pyppeteer = False
try:
    from pyppeteer import launch
    import_pyppeteer = True
except Exception as e:
    # Fix ldd ~/.local/share/pyppeteer/local-chromium/1181205/chrome-linux/chrome | grep not
    # apt install libgbm-dev
    # See https://techoverflow.net/2020/09/29/how-to-fix-pyppeteer-pyppeteer-errors-browsererror-browser-closed-unexpectedly/
    logger.info('For better URL parsing, try `pip install pyppeteer` and see https://github.com/pyppeteer/pyppeteer/issues/442')

async def fetch_chroumium_content(url):
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-software-rasterizer', '--disable-setuid-sandbox'])
    page = await browser.newPage()
    await page.goto(url)
    time.sleep(1)
    content = await page.evaluate('document.body.innerText', force_expr=True)
    await browser.close()
    return content

class Article:

    def __init__(self, content: str = '', source='', brief=''):
        self.content = content
        self.source = source
        if len(brief) < 1:
            self.brief = content
        else:
            self.brief = brief

    def __str__(self):
        return self.content

    def __len__(self):
        return len(self.content)

    def cut(self, start_index, end_index):
        self.source = self.source[start_index:end_index]


class WebSearch:
    """This class provides functionality to perform web search operations.

    Attributes:
        config_path (str): Path to the configuration file.
        retry (int): Number of times to retry a request before giving up.

    Methods:
        load_key(): Retrieves API key from the config file.
        load_save_dir(): Gets the directory path for saving results.
        google(query: str, max_article:int): Performs Google search for the given query and returns top max_article results.  # noqa E501
        save_search_result(query:str, articles: list): Saves the search result into a text file.  # noqa E501
        get(query: str, max_article=1): Searches with cache. If the query already exists in the cache, return the cached result.  # noqa E501
    """

    def __init__(self, config_path: str, retry: int = 1) -> None:
        """Initializes the WebSearch object with the given config path and
        retry count."""

        self.search_config = None
        with open(config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            self.search_config = types.SimpleNamespace(**config['web_search'])
        self.retry = retry

    def fetch_url(self, query: str, target_link: str, brief: str = ''):
        if not target_link.startswith('http'):
            return None

        logger.info(f'extract: {target_link}')
        try:
            content = ''
            response = requests.get(target_link, timeout=30)

            doc = Document(response.text)
            content_html = doc.summary()
            title = doc.short_title()
            soup = BS(content_html, 'html.parser')

            if len(soup.text) < 4 * len(query):
                return None
            content = '{} {}'.format(title, soup.text)
            content = content.replace('\n\n', '\n')
            content = content.replace('\n\n', '\n')
            content = content.replace('  ', ' ')

            if not check_str_useful(content=content):
                logger.info('retry with chromium {}'.format(target_link))
                nest_asyncio.apply()
                content = asyncio.get_event_loop().run_until_complete(fetch_chroumium_content(url=target_link))
                if not check_str_useful(content=content):
                    return None

            return Article(content=content, source=target_link, brief=brief)
        except Exception as e:
            logger.error('fetch_url {}'.format(str(e)))
        return None

    def ddgs(self, query: str, max_article: int):
        """Run DDGS search based on query."""
        results = DDGS().text(query, max_results=20)
        filter_results = []

        for domain in self.search_config.domain_partial_order:
            for result in results:
                if domain in result['href']:
                    filter_results.append(result)
                    break

        logger.debug('filter results: {}'.format(filter_results))
        articles = []
        for result in filter_results:
            a = self.fetch_url(query=query,
                               target_link=result['href'],
                               brief=result['body'])
            if a is not None and len(a) > 0:
                articles.append(a)
            if len(articles) > max_article:
                break
        return articles

    def google(self, query: str, max_article: int):
        """Executes a google search based on the provided query.

        Parses the response and extracts the relevant URLs based on the
        priority defined in the configuration file. Performs a GET request on
        these URLs and extracts the title and content of the page. The content
        is cleaned and added to the articles list. Returns a list of articles.
        """
        url = 'https://google.serper.dev/search'

        payload = json.dumps({'q': f'{query}', 'hl': 'zh-cn'})
        headers = {
            'X-API-KEY': self.search_config.serper_x_api_key,
            'Content-Type': 'application/json'
        }
        response = requests.request('POST',
                                    url,
                                    headers=headers,
                                    data=payload,
                                    timeout=15)  # noqa E501
        jsonobj = json.loads(response.text)
        logger.debug(jsonobj)
        keys = self.search_config.domain_partial_order
        urls = {}
        normal_urls = []

        for organic in jsonobj['organic']:
            link = ''
            logger.debug(organic)

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
                else:
                    normal_urls.append(link)

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
            a = self.fetch_url(query=query, target_link=target_link)
            if a is not None:
                articles.append(a)

        return articles

    def save_search_result(self, query: str, articles: list):
        """Writes the search results (articles) for the provided query into a
        text file.

        If the directory does not exist, it creates one. In case of an error,
        logs a warning message.
        """
        try:
            save_dir = self.search_config.save_dir
            if save_dir is None:
                return

            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            filepath = os.path.join(save_dir, query)

            text = ''
            if len(articles) > 0:
                texts = [str(a) for a in articles]
                text = '\n\n'.join(texts)
            with open(filepath, 'w', encoding='utf8') as f:
                f.write(text)
        except Exception as e:
            logger.warning(f'error while saving search result {str(e)}')

    def logging_search_query(self, query: str):
        """Logging search query to txt file."""

        save_dir = self.search_config.save_dir
        if save_dir is None:
            return

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        filepath = os.path.join(save_dir, 'search_query.txt')
        with open(filepath, 'a') as f:
            f.write(query)
            f.write('\n')

    def get(self, query: str, max_article=1):
        """Executes a google search with cache.

        If the query already exists in the cache, returns the cached result. If
        an exception occurs during the process, retries the request based on
        the retry count. Sleeps for a random time interval between retries.
        """
        query = query.strip()
        query = query[0:32]

        try:
            self.logging_search_query(query=query)

            articles = []
            engine = self.search_config.engine.lower()
            if engine == 'ddgs':
                articles = self.ddgs(query=query, max_article=max_article)

            elif engine == 'serper':
                articles = self.google(query=query, max_article=max_article)

            self.save_search_result(query=query, articles=articles)

            return articles, None
        except Exception as e:
            logger.error(('web_search exception', query, str(e)))
            return [], Exception('search fail, please check TOKEN')
        return [], None


def parse_args():
    """Parses command-line arguments for web search."""
    parser = argparse.ArgumentParser(description='Web search.')
    parser.add_argument('--keywords',
                        type=str,
                        help='Keywords for search and parse.')
    parser.add_argument(
        '--config_path',
        default='config.ini',
        help='Feature store configuration path. Default value is config.ini')
    args = parser.parse_args()
    return args


def fetch_web_content(target_link: str):
    """Fetches and parses the content of the target URL.

    Extracts the main content and title from the HTML of the page. Returns the
    title and content as a single string.
    """
    response = requests.get(target_link, timeout=60)

    doc = Document(response.text)
    content_html = doc.summary()
    title = doc.short_title()
    soup = BS(content_html, 'html.parser')
    ret = '{} {}'.format(title, soup.text)
    return ret


if __name__ == '__main__':
    # https://developer.aliyun.com/article/679591 failed
    # print(fetch_web_content('https://www.volcengine.com/theme/4222537-R-7-1'))

    parser = parse_args()
    s = WebSearch(config_path=parser.config_path)
    print(s.fetch_url(query='', target_link='https://zhuanlan.zhihu.com/p/699164101'))
    print(s.get('LMDeploy 修改日志级别'))
    print(
        fetch_web_content(
            'https://mmdeploy.readthedocs.io/zh-cn/latest/get_started.html'))
