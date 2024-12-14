from app.models.db import Database

def test_connection():
    print("开始测试连接...")
    try:
        print("正在创建数据库连接...")
        db = Database()
        print("执行测试查询...")
        db.execute_query("SELECT 1")
        result = db.cursor.fetchone()
        print("数据库连接成功！")
        db.close()
    except Exception as e:
        print(f"连接错误：{e}")

if __name__ == "__main__":
    print("程序开始运行")
    test_connection()
    print("程序结束")