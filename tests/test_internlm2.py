import pdb

from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = '/internlm/ampere_7b_v1_7_0'

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path,
                                             trust_remote_code=True,
                                             device_map='auto',
                                             torch_dtype='auto').eval()

# 不能像某些 LLM 一样 AutoModelForCausalLM.from_pretrained(.. fp16=True) 这样写，会 Internlm2Config.__init__() 报错

queries = ['how to install mmdeploy ?']
for query in queries:
    pdb.set_trace()
    output_text, _ = model.chat(tokenizer, query, top_k=1, do_sample=False)
    print(query, output_text)
