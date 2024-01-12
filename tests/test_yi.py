from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained('/models/Yi-6B-200K',
                                             device_map='auto',
                                             torch_dtype='auto',
                                             trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained('/models/Yi-6B-200K',
                                          trust_remote_code=True)
inputs = tokenizer('', return_tensors='pt')
max_length = 512
outputs = model.generate(
    inputs.input_ids.cuda(),
    max_length=max_length,
    eos_token_id=tokenizer.eos_token_id,
    do_sample=True,
    repetition_penalty=1.3,
    no_repeat_ngram_size=5,
    temperature=0.7,
    top_k=1,
    top_p=0.8,
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
