import argparse
import json
import time
from aiohttp import web

import gradio as gr
import pytoml
import markdown
from loguru import logger

from huixiangdou.service import ErrorCode, Worker, llm_serve, start_llm_server

html_begin = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>问答</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid black;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>

    <h2>问答表格</h2>

    <table>
        <tr>
            <th>问题</th>
            <th>答复</th>
            <th>参考文档</th>
            <th>状态码</th>
        </tr>
        <tr>"""

html_end="""
        </tr>
    </table>
</body>
</html>"""

html_template="<td>{query}</td><td>{resp}</td><td>{refs}</td><td>{code}</td>"

assistant = Worker(work_dir='workdir', config_path='config.ini')

def inference(request):
    """Call local llm inference."""

    query = request.rel_url.query['query']
    code, resp, refs = assistant.generate(query=query, history=[], groupname='')
    logger.info(resp)
    resp_html = markdown.markdown(resp)
    html_str = html_begin + html_template.format(query=str(query), resp=str(resp_html), refs=json.dumps(refs, ensure_ascii=False), code=str(code)) + html_end
    return web.Response(text=html_str, content_type='text/html')

app = web.Application()
app.add_routes([web.get('/inference', inference)])
web.run_app(app, host='0.0.0.0', port=9999)

# queries = ['水稻可以在海水中种植吗？', '五常大米是国外引进品种吗？', '浙辐802适合在哪些地区种植？']
# for query in queries:
#     logger.info(assistant.generate(query=query, history=[], groupname=''))
#     logger.info(query)
