import asyncio
from pyppeteer import launch
import time

async def main(url):
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-software-rasterizer', '--disable-setuid-sandbox'])
    page = await browser.newPage()
    await page.goto(url)
    content = await page.evaluate('document.getElementsByClassName("Post-Main")[0].innerText', force_expr=True)
    # print(content)
    await browser.close()
    return content

result = asyncio.get_event_loop().run_until_complete(main(url='https://zhuanlan.zhihu.com/p/699164101'))
print(result)
