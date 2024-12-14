import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123123'),
    'database': os.getenv('DB_NAME', 'library_system'),
    'charset': 'utf8mb4'
}

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')