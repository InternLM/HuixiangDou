import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import asyncio

# wrap to async generator
async def chat_stream():
    model_path = "/data2/khj/internlm2_5-7b-chat"
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, trust_remote_code=True).cuda()
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    model = model.eval()
    length = 0
    for response, history in model.stream_chat(tokenizer, "Hello", history=[]):
        part = response[length:]
        length = len(response)
        yield part
    yield '\n'

# coroutine
async def main():
    async for part in chat_stream():
        print(part, flush=True, end="")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())