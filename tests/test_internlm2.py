from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = '/internlm/ampere_7b_v1_7_0'

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path,
                                             trust_remote_code=True,
                                             device_map='auto',
                                             torch_dtype='auto').eval()

queries = ['how to install mmdeploy ?']
for query in queries:
    output_text, _ = model.chat(tokenizer, query, top_k=1, do_sample=False)
    print(query, output_text)
