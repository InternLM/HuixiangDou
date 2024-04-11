# Copyright (c) OpenMMLab. All rights reserved.
"""Web search utils."""
import argparse
import json
import os

import pytoml
import requests
from bs4 import BeautifulSoup as BS
from loguru import logger
from readability import Document


class Article:

    def __init__(self, content: str = '', source=''):
        self.content = content
        self.source = source

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
        load_urls(): Loads URLs from config file.
        load_key(): Retrieves API key from the config file.
        load_save_dir(): Gets the directory path for saving results.
        google(query: str, max_article:int): Performs Google search for the given query and returns top max_article results.  # noqa E501
        save_search_result(query:str, articles: list): Saves the search result into a text file.  # noqa E501
        get(query: str, max_article=1): Searches with cache. If the query already exists in the cache, return the cached result.  # noqa E501
    """

    def __init__(self, config_path: dict, retry: int = 2) -> None:
        """Initializes the WebSearch object with the given config path and
        retry count."""
        self.config_path = config_path
        self.retry = retry

    def load_urls(self):
        """Reads the configuration file and fetches the ordered URLs.

        In case of an error, logs the exception and returns an empty list.
        """
        try:
            with open(self.config_path, encoding='utf8') as f:
                config = pytoml.load(f)
                return config['web_search']['domain_partial_order']
        except Exception as e:
            logger.error(str(e))
        return []

    def load_key(self):
        """Attempts to load the API key from the configuration file.

        Raises an Exception if it fails to find a valid API key.
        """
        with open(self.config_path, encoding='utf8') as f:
            config = pytoml.load(f)
            api_key = config['web_search']['x_api_key']
            # if len(api_key) > 0 and 'YOUR-API-KEY' not in api_key:
            return api_key
        raise Exception(
            'web_search X-API-KEY not found, please input your API key')

    def load_save_dir(self):
        """Attempts to read the directory where the search results are stored
        from the configuration file.

        Returns None if it fails.
        """
        try:
            with open(self.config_path, encoding='utf8') as f:
                config = pytoml.load(f)
                return config['web_search']['save_dir']
        except Exception:
            pass
        return None

    def fetch_url(self, query: str, target_link: str):
        if not target_link.startswith('http'):
            return None

        logger.info(f'extract: {target_link}')
        try:
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

            return Article(content=content, source=target_link)
        except Exception as e:
            logger.error('fetch_url {}'.format(str(e)))
        return None

    def google(self, query: str, max_article):
        """Executes a google search based on the provided query.

        Parses the response and extracts the relevant URLs based on the
        priority defined in the configuration file. Performs a GET request on
        these URLs and extracts the title and content of the page. The content
        is cleaned and added to the articles list. Returns a list of articles.
        """
        url = 'https://google.serper.dev/search'

        payload = json.dumps({'q': f'{query}', 'hl': 'zh-cn'})
        headers = {
            'X-API-KEY': self.load_key(),
            'Content-Type': 'application/json'
        }
        response = requests.request('POST',
                                    url,
                                    headers=headers,
                                    data=payload,
                                    timeout=15)  # noqa E501
        jsonobj = json.loads(response.text)

        keys = self.load_urls()
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
            save_dir = self.load_save_dir()
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

    def get(self, query: str, max_article=1):
        """Executes a google search with cache.

        If the query already exists in the cache, returns the cached result. If
        an exception occurs during the process, retries the request based on
        the retry count. Sleeps for a random time interval between retries.
        """
        query = query.strip()
        query = query[0:32]
        try:
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
    parser = parse_args()
    s = WebSearch(config_path=parser.config_path)

    print(s.get('mmdeploy 安装教程'))
    print(
        fetch_web_content(
            'https://mmdeploy.readthedocs.io/zh-cn/latest/get_started.html'))
