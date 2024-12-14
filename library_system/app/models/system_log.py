from .db import Database

class SystemLog:
    @staticmethod
    def get_logs(db: Database, limit=None):
        if limit:
            db.execute_query("SELECT * FROM system_logs ORDER BY created_at DESC LIMIT %s", (limit,))
        else:
            db.execute_query("SELECT * FROM system_logs ORDER BY created_at DESC")
            
        return db.cursor.fetchall()