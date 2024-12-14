from app.models.db import Database
from werkzeug.security import generate_password_hash

def update_password(username, new_password):
    print(f"开始更新用户 {username} 的密码...")
    db = Database()
    try:
        hashed_password = generate_password_hash(new_password)
        db.execute_query("""
            UPDATE users 
            SET password = %s 
            WHERE username = %s
        """, (hashed_password, username))
        
        if db.cursor.rowcount > 0:
            db.commit()
            print("密码更新成功！")
        else:
            print("未找到该用户！")
            
    except Exception as e:
        print(f"错误：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    username = input("请输入用户名: ")
    new_password = input("请输入新密码: ")
    update_password(username, new_password) 