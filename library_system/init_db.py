from app.models.db import Database

def init_database():
    print("开始初始化数据库...")
    db = Database()
    try:
        # 创建用户表
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_username (username)
            )
        """)
        
        # 创建出版社表
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS publishers (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL
            )
        """)
        
        # 创建分类表
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(50) NOT NULL
            )
        """)
        
        # 创建图书表
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS books (
                id INT PRIMARY KEY AUTO_INCREMENT,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100) NOT NULL,
                isbn VARCHAR(13) UNIQUE NOT NULL,
                price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                stock INT NOT NULL DEFAULT 0,
                publisher_id INT,
                category_id INT,
                published_date DATE,
                FOREIGN KEY (publisher_id) REFERENCES publishers(id),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                INDEX idx_isbn (isbn)
            )
        """)
        
        # 创建系统日志表
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                operation VARCHAR(50) NOT NULL,
                details TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建借阅记录表
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS borrowings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                book_id INT NOT NULL,
                borrow_date DATE NOT NULL,
                return_date DATE,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (book_id) REFERENCES books(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db.commit()
        print("数据库表创建成功！")
    except Exception as e:
        print(f"错误：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()