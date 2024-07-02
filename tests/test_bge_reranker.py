from FlagEmbedding import FlagReranker

reranker = FlagReranker(
    '/data2/khj/bge-reranker-v2-m3/', use_fp16=True
)  # Setting use_fp16 to True speeds up computation with a slight performance degradation

score = reranker.compute_score(['query', 'passage'])
print(score)  # -5.65234375

# You can map the scores into 0-1 by set "normalize=True", which will apply sigmoid function to the score
score = reranker.compute_score(['query', 'passage'], normalize=True)
print(score)  # 0.003497010252573502

scores = reranker.compute_score([
    ['what is panda?', 'hi'],
    [
        'what is panda?',
        'The giant panda (Ailuropoda melanoleuca), sometimes called a panda bear or simply panda, is a bear species endemic to China.'
    ]
])
print(scores)  # [-8.1875, 5.26171875]
import pdb

pdb.set_trace()
# You can map the scores into 0-1 by set "normalize=True", which will apply sigmoid function to the score
scores = reranker.compute_score([
    ['what is panda?', 'hi'],
    [
        'what is panda?',
        'The giant panda (Ailuropoda melanoleuca), sometimes called a panda bear or simply panda, is a bear species endemic to China.'
    ]
],
                                normalize=True)
print(scores)  # [0.00027803096387751553, 0.9948403768236574]
