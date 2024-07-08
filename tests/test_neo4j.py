from neo4j import GraphDatabase
# Neo4j Desktop 版
# 1. 关掉 auth
# 2. server.default_listen_address=0.0.0.0
# 浏览器打开 http://10.1.52.85:7474/browser/，无密码模式应该能登录

# 配置 Neo4j 连接参数
uri = "bolt://10.1.52.85:7687"  # 默认的 bolt 协议地址和端口
user = "neo4j"                 # Neo4j 用户名
password = "neo4j"     # Neo4j 密码

# 创建驱动实例
driver = GraphDatabase.driver(uri, auth=(user, password))

try:
    # 运行一个简单的查询，比如返回所有节点
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n LIMIT 1")
        print("Query result:", [record for record in result])
except Exception as e:
    print("An error occurred:", e)
finally:
    # 确保关闭驱动连接
    driver.close()