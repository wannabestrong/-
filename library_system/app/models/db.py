import mysql.connector
from config import MYSQL_CONFIG

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(**MYSQL_CONFIG)
        self.cursor = self.connection.cursor(dictionary=True)
    
    def execute_query(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor
    
    def commit(self):
        self.connection.commit()
    
    def rollback(self):
        self.connection.rollback()
    
    def close(self):
        self.cursor.close()
        self.connection.close() 