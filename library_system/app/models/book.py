from .db import Database
from typing import List, Dict, Any

class Book:
    def __init__(self, id=None, title=None, isbn=None):
        self.id = id
        self.title = title
        self.isbn = isbn
    
    @staticmethod
    def get_by_id(db: Database, book_id: int):
        db.execute_query("""
            SELECT b.*, p.name as publisher_name, c.name as category_name,
            (SELECT COUNT(*) FROM borrowings 
             WHERE book_id = b.id AND return_date IS NULL) as is_borrowed
            FROM books b
            LEFT JOIN publishers p ON b.publisher_id = p.id
            LEFT JOIN categories c ON b.category_id = c.id
            WHERE b.id = %s
        """, (book_id,))
        return db.cursor.fetchone()
    
    @staticmethod
    def get_all(db: Database, page: int = 1, per_page: int = 10):
        offset = (page - 1) * per_page
        db.execute_query("""
            SELECT b.*, p.name as publisher_name, c.name as category_name,
            (SELECT COUNT(*) FROM borrowings 
             WHERE book_id = b.id AND return_date IS NULL) as is_borrowed
            FROM books b
            LEFT JOIN publishers p ON b.publisher_id = p.id
            LEFT JOIN categories c ON b.category_id = c.id
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        return db.cursor.fetchall() 
    
    @staticmethod
    def batch_update_stock(db: Database, updates: List[Dict[str, Any]]) -> bool:
        """批量更新图书库存"""
        try:
            db.begin_transaction()
            for update in updates:
                db.execute_query("""
                    UPDATE books 
                    SET stock = stock + %s 
                    WHERE id = %s AND stock + %s >= 0
                """, (update['change'], update['book_id'], update['change']))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_stock_alerts(db: Database) -> List[Dict]:
        """获取库存预警信息"""
        db.execute_query("""
            SELECT * FROM vw_book_stock_alert
        """)
        return db.cursor.fetchall()

    @staticmethod
    def batch_delete(db: Database, book_ids: List[int]) -> bool:
        """批量删除图书"""
        try:
            db.begin_transaction()
            # 检查是否有未还的借阅
            db.execute_query("""
                SELECT book_id FROM borrowings 
                WHERE book_id IN %s AND return_date IS NULL
            """, (tuple(book_ids),))
            
            borrowed_books = db.cursor.fetchall()
            if borrowed_books:
                raise Exception("有图书尚未归还，无法删除")
                
            db.execute_query("""
                DELETE FROM books WHERE id IN %s
            """, (tuple(book_ids),))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_with_log(db: Database, book_id: int, updates: Dict[str, Any]) -> bool:
        """更新图书信息（带日志）"""
        try:
            db.begin_transaction()
            set_clauses = []
            params = []
            for key, value in updates.items():
                if key in ['title', 'author', 'isbn', 'price', 'stock']:
                    set_clauses.append(f"{key} = %s")
                    params.append(value)
            
            if set_clauses:
                params.append(book_id)
                query = f"""
                    UPDATE books 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                db.execute_query(query, tuple(params))
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e 