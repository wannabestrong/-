from app.models.db import Database
from werkzeug.security import generate_password_hash
import random
from datetime import datetime, timedelta
import faker

fake = faker.Faker(['zh_CN'])

def generate_test_data():
    print("开始生成测试数据...")
    db = Database()
    try:
        # 1. 生成用户数据 (1000个用户)
        print("正在生成用户数据...")
        users = []  # 存储生成的用户ID
        
        # 先获取已存在的用户数量
        db.execute_query("SELECT COUNT(*) as count FROM users")
        existing_users = db.cursor.fetchone()['count']
        start_index = existing_users  # 从现有用户数量开始计数
        
        for i in range(start_index, start_index + 1000):
            username = f'user_{i}'
            # 检查用户名是否已存在
            db.execute_query("SELECT id FROM users WHERE username = %s", (username,))
            if not db.cursor.fetchone():
                db.execute_query("""
                    INSERT INTO users (username, password, email, created_at) 
                    VALUES (%s, %s, %s, %s)
                """, (
                    username,
                    generate_password_hash(f'password_{i}'),
                    f'user_{i}@example.com',
                    fake.date_time_between(start_date='-2y')
                ))
                users.append(db.cursor.lastrowid)
                if i % 100 == 0:
                    print(f"已生成 {i-start_index} 个用户")
                    db.commit()
        
        # 2. 生成出版社数据 (50个出版社)
        print("正在生成出版社数据...")
        publishers = []
        # 获取现有出版社
        db.execute_query("SELECT id FROM publishers")
        publishers = [row['id'] for row in db.cursor.fetchall()]
        
        if len(publishers) < 50:
            for i in range(50 - len(publishers)):
                name = fake.company() + "出版社"
                db.execute_query("SELECT id FROM publishers WHERE name = %s", (name,))
                if not db.cursor.fetchone():
                    db.execute_query("""
                        INSERT INTO publishers (name) VALUES (%s)
                    """, (name,))
                    publishers.append(db.cursor.lastrowid)
        db.commit()
        print(f"出版社数据已就绪，共 {len(publishers)} 家出版社")
            
        # 3. 生成分类数据 (20个分类)
        print("正在生成分类数据...")
        categories = []
        # 获取现有分类
        db.execute_query("SELECT id FROM categories")
        categories = [row['id'] for row in db.cursor.fetchall()]
        
        category_names = ['计算机', '文学', '历史', '科技', '艺术', '教育', '经济', 
                         '哲学', '政治', '军事', '医学', '工程', '农业', '环境',
                         '社会科学', '心理学', '语言', '地理', '物理', '化学']
        
        if len(categories) < 20:
            for category in category_names:
                db.execute_query("SELECT id FROM categories WHERE name = %s", (category,))
                if not db.cursor.fetchone():
                    db.execute_query("""
                        INSERT INTO categories (name) VALUES (%s)
                    """, (category,))
                    categories.append(db.cursor.lastrowid)
        db.commit()
        print(f"分类数据已就绪，共 {len(categories)} 个分类")

        # 4. 生成图书数据 (5000本书)
        print("正在生成图书数据...")
        books = []
        # 获取现有图书
        db.execute_query("SELECT id FROM books")
        books = [row['id'] for row in db.cursor.fetchall()]
        
        remaining_books = 5000 - len(books)
        if remaining_books > 0:
            for i in range(remaining_books):
                title = fake.catch_phrase()
                author = fake.name()
                isbn = f'978{fake.random_number(digits=10)}'
                
                # 检查ISBN是否已存在
                db.execute_query("SELECT id FROM books WHERE isbn = %s", (isbn,))
                if not db.cursor.fetchone():
                    price = round(random.uniform(20, 200), 2)
                    stock = random.randint(0, 100)
                    publisher_id = random.choice(publishers)
                    category_id = random.choice(categories)
                    published_date = fake.date_between(start_date='-10y')
                    
                    db.execute_query("""
                        INSERT INTO books (title, author, isbn, price, stock, 
                                         publisher_id, category_id, published_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (title, author, isbn, price, stock, publisher_id, 
                          category_id, published_date))
                    books.append(db.cursor.lastrowid)
                    if i % 500 == 0:
                        print(f"已生成 {i} 本图书")
                        db.commit()
        print(f"图书数据已就绪，共 {len(books)} 本图书")

        # 5. 生成借阅记录 (10000条记录)
        print("正在生成借阅记录...")
        # 获取现有借阅记录数量
        db.execute_query("SELECT COUNT(*) as count FROM borrowings")
        existing_borrowings = db.cursor.fetchone()['count']
        remaining_borrowings = 10000 - existing_borrowings
        
        if remaining_borrowings > 0:
            for i in range(remaining_borrowings):
                user_id = random.choice(users)
                book_id = random.choice(books)
                borrow_date = fake.date_time_between(start_date='-1y')
                return_date = None
                if random.random() > 0.3:  # 70%的概率已归还
                    return_date = borrow_date + timedelta(days=random.randint(1, 30))
                
                try:
                    db.execute_query("""
                        INSERT INTO borrowings (user_id, book_id, borrow_date, return_date)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, book_id, borrow_date, return_date))
                    if i % 1000 == 0:
                        print(f"已生成 {i} 条借阅记录")
                        db.commit()
                except Exception as e:
                    print(f"插入借阅记录失败: user_id={user_id}, book_id={book_id}, error={str(e)}")
                    continue

        db.commit()
        print("测试数据生成完成！")
        
    except Exception as e:
        print(f"错误：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_data()