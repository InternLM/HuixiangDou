import os
import pdb

from openai import OpenAI
from tqdm import tqdm

client = OpenAI(api_key=os.getenv('MOONSHOT_API_KEY'),
                base_url='https://api.moonshot.cn/v1')
file_list = client.files.list()
for file in tqdm(file_list.data):
    client.files.delete(file_id=file.id)
    print(file)
