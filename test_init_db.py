# test_init_db.py 每运行一次，新增一条数据
from database import SessionLocal, UserRecord

db = SessionLocal() # 创建一个数据库会话（Session）
new_user = UserRecord(name="syj", api_key_value="123") # 在内存里创建一个 UserRecord 对象。此时数据还在 Python 里，没进数据库。
db.add(new_user) #将对象加入会话
db.commit() # 提交会话，将数据写入数据库
db.close() # 关闭会话
print("初始数据添加成功！")