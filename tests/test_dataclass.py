import pdb
from enum import Enum, unique


@unique
class KGType(Enum):
    MARKDOWN = 'markdown'
    CHUNK = 'chunk'
    KEYWORD = 'keyword'
    IMAGE = 'image'


x = KGType.IMAGE

pdb.set_trace()
print(x)
