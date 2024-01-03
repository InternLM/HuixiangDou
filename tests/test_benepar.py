import benepar
benepar.download('benepar_en3_large')
import nltk
nltk.download('punkt')
# 创建解析器
parser = benepar.Parser("benepar_en3_large")

# 解析句子
tree = parser.parse("The quick brown fox jumps over the lazy dog.")