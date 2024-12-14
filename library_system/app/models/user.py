from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db import Database

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    @staticmethod
    def create(db: Database, username: str, password: str, email: str):
        hashed_password = generate_password_hash(password)
        try:
            db.execute_query("""
                INSERT INTO users (username, password, email)
                VALUES (%s, %s, %s)
            """, (username, hashed_password, email))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_by_id(db: Database, user_id: int):
        db.execute_query("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = db.cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email']
            )
        return None 
    
    @staticmethod
    def get_by_username(db, username):
        db.execute_query("SELECT * FROM users WHERE username = %s", (username,))
        user_data = db.cursor.fetchone()
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
        return None 