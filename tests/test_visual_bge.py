##### Use M3 doing Multilingual Multi-Modal Retrieval
import torch
from FlagEmbedding.visual.modeling import Visualized_BGE

model = Visualized_BGE(
    model_name_bge='/data2/khj/bge-m3',
    model_weight='/data2/khj/bge-visualized/Visualized_m3.pth')
model.eval()
with torch.no_grad():
    query_emb = model.encode(image='./imgs/cir_query.png', text='一匹马牵着这辆车')
    candi_emb_1 = model.encode(image='./imgs/cir_candi_1.png')
    candi_emb_2 = model.encode(image='./imgs/cir_candi_2.png')

sim_1 = query_emb @ candi_emb_1.T
sim_2 = query_emb @ candi_emb_2.T
print(sim_1, sim_2)  # tensor([[0.7026]]) tensor([[0.8075]])
