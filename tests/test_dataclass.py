from enum import Enum, unique
import pdb

@unique
class KGType(Enum):
    MARKDOWN = 'markdown'
    CHUNK = 'chunk'
    KEYWORD = 'keyword'
    IMAGE = 'image'

x = KGType.IMAGE

pdb.set_trace()
print(x)