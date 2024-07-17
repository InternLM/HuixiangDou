import nxneo4j as nx
from neo4j import GraphDatabase

# Neo4j Desktop 版
# 1. 关掉 auth
# 2. server.default_listen_address=0.0.0.0
# 浏览器打开 http://10.1.52.85:7474/browser/，无密码模式应该能登录

# 配置 Neo4j 连接参数
uri = 'bolt://10.1.52.85:7687'  # 默认的 bolt 协议地址和端口
user = 'neo4j'  # Neo4j 用户名
password = 'neo4j'  # Neo4j 密码

# 创建驱动实例
driver = GraphDatabase.driver(uri, auth=(user, password))

G = nx.Graph(driver)
G.delete_all()

#Add a node
G.add_node('Yusuf')
#Add node with features
G.add_node('Nurgul', gender='F')
#Add multiple properties at once
G.add_node('Betul', age=4, gender='F')
#Check nodes
for node in G.nodes():  #Unlike networkX, nxneo4j returns a generator
    print(node)
