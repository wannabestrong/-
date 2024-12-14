from app.models.db import Database
from werkzeug.security import generate_password_hash

def reset_password():
    username = 'admin'  # 要修改的用户名
    new_password = '123456'  # 新密码
    
    print(f"开始重置 {username} 的密码...")
    db = Database()
    try:
        # 生成加密密码
        hashed_password = generate_password_hash(new_password)
        
        # 更新密码
        db.execute_query("""
            UPDATE users 
            SET password = %s 
            WHERE username = %s
        """, (hashed_password, username))
        
        # 提交更改
        db.commit()
        print("密码重置成功！")
        print(f"用户名: {username}")
        print(f"新密码: {new_password}")
        
    except Exception as e:
        print(f"错误：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_password() 