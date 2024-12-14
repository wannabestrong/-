from app.models.db import Database
from werkzeug.security import generate_password_hash

def insert_test_data():
    print("开始插入测试数据...")
    db = Database()
    try:
        # 检查并插入测试用户
        db.execute_query("SELECT username FROM users WHERE username = 'admin'")
        if not db.cursor.fetchone():
            db.execute_query("""
                INSERT INTO users (username, password, email) VALUES 
                ('admin', %s, 'admin@example.com'),
                ('user1', %s, 'user1@example.com'),
                ('user2', %s, 'user2@example.com')
            """, (
                generate_password_hash('admin123'),
                generate_password_hash('user123'),
                generate_password_hash('user123')
            ))
        
        # 检查并插入出版社
        db.execute_query("SELECT name FROM publishers WHERE name = '人民出版社'")
        if not db.cursor.fetchone():
            db.execute_query("""
                INSERT INTO publishers (name) VALUES 
                ('人民出版社'),
                ('商务印书馆'),
                ('机械工业出版社')
            """)
        
        # 检查并插入图书分类
        db.execute_query("SELECT name FROM categories WHERE name = '计算机'")
        if not db.cursor.fetchone():
            db.execute_query("""
                INSERT INTO categories (name) VALUES 
                ('计算机'),
                ('文学'),
                ('历史'),
                ('科技')
            """)
        
        # 检查并插入图书
        db.execute_query("SELECT isbn FROM books WHERE isbn = '9787111111111'")
        if not db.cursor.fetchone():
            db.execute_query("""
                INSERT INTO books (title, author, isbn, price, stock, publisher_id, category_id) VALUES 
                ('Python编程', '张三', '9787111111111', 59.00, 10, 3, 1),
                ('三国演义', '罗贯中', '9787111111112', 45.00, 15, 1, 2),
                ('中国历史', '李四', '9787111111113', 68.00, 8, 2, 3),
                ('人工智能', '王五', '9787111111114', 88.00, 12, 3, 4),
                ('数据库系统', '赵六', '9787111111115', 75.00, 20, 3, 1)
            """)
        
        db.commit()
        print("测试数据插入成功！")
        
    except Exception as e:
        print(f"错误：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_data()