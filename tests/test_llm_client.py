import aiohttp
import asyncio
import json
import pdb

async def post_event_source(url, prompt, history, backend):
    # 准备POST请求的headers和数据
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'history': history,
        'backend': backend
    }

    # 发送POST请求
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as response:
            # 确保请求成功
            if response.status == 200:
                # 处理SSE响应
                async for chunk in response.content.iter_any():
                    chunk_str = chunk.decode().strip()
                    mines = chunk_str.split('\r\n\r\n')

                    for mime_str in mines:
                        pos = mime_str.find('data: ') + len('data: ')
                        content = mime_str[pos:]
                        print(content, end='', flush=True)
            else:
                print(f"Failed to connect: {response.status}")

async def post_single(url, prompt, history, backend):
    # 准备POST请求的headers和数据
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'history': history,
        'backend': backend
    }

    # 发送POST请求
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as response:
            # 确保请求成功
            if response.status == 200:
                async for chunk in response.content.iter_any():
                    chunk_str = chunk.decode().strip()
                    print(chunk_str, end='', flush=True)
            else:
                print(f"Failed to connect: {response.status}")

# 使用示例
async def main():
    prompt = 'What is the weather like today?'
    history = []
    backend = 'local'

    # await post_event_source('http://10.1.52.22:8888/stream_chat', prompt, history, backend)
    await post_single('http://10.1.52.22:8888/inference', prompt, history, backend)

# 运行异步main函数
if __name__ == '__main__':
    asyncio.run(main())