from datetime import datetime, timedelta
from typing import List, Dict, Any
from .db import Database

class Borrowing:
    @staticmethod
    def get_pending_approvals(db: Database) -> List[Dict]:
        """获取待审批的借阅申请"""
        db.execute_query("""
            SELECT b.*, u.username, bk.title as book_title
            FROM borrowings b
            JOIN users u ON b.user_id = u.id
            JOIN books bk ON b.book_id = bk.id
            WHERE b.status = 'pending'
            ORDER BY b.created_at DESC
        """)
        return db.cursor.fetchall()

    @staticmethod
    def approve(db: Database, borrowing_id: int, approved: bool) -> bool:
        """审批借阅申请"""
        try:
            db.begin_transaction()
            if approved:
                # 检查库存
                db.execute_query("""
                    SELECT b.book_id, bk.stock, 
                           COUNT(other_b.id) as current_borrowed
                    FROM borrowings b
                    JOIN books bk ON b.book_id = bk.id
                    LEFT JOIN borrowings other_b ON b.book_id = other_b.book_id 
                        AND other_b.return_date IS NULL
                    WHERE b.id = %s
                    GROUP BY b.book_id, bk.stock
                    FOR UPDATE
                """, (borrowing_id,))
                
                stock_info = db.cursor.fetchone()
                if stock_info['stock'] - stock_info['current_borrowed'] <= 0:
                    raise Exception("库存不足")

                status = 'approved'
            else:
                status = 'rejected'
                
            db.execute_query("""
                UPDATE borrowings 
                SET status = %s,
                    approved_at = NOW(),
                    borrow_date = CASE WHEN %s = 'approved' THEN CURRENT_DATE ELSE NULL END
                WHERE id = %s
            """, (status, status, borrowing_id))
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_statistics(db: Database) -> Dict[str, Any]:
        """获取借阅统计信息"""
        stats = {}
        
        # 总借阅量统计
        db.execute_query("""
            SELECT 
                COUNT(*) as total_borrows,
                COUNT(CASE WHEN return_date IS NULL THEN 1 END) as current_borrowed,
                COUNT(DISTINCT user_id) as total_users,
                COUNT(DISTINCT book_id) as total_books
            FROM borrowings
        """)
        stats['overview'] = db.cursor.fetchone()
        
        # 最受欢迎的图书
        db.execute_query("""
            SELECT book_id, books.title, COUNT(*) as borrow_count
            FROM borrowings
            JOIN books ON borrowings.book_id = books.id
            GROUP BY book_id, books.title
            ORDER BY borrow_count DESC
            LIMIT 10
        """)
        stats['popular_books'] = db.cursor.fetchall()
        
        # 活跃用户
        db.execute_query("""
            SELECT user_id, users.username, COUNT(*) as borrow_count
            FROM borrowings
            JOIN users ON borrowings.user_id = users.id
            GROUP BY user_id, users.username
            ORDER BY borrow_count DESC
            LIMIT 10
        """)
        stats['active_users'] = db.cursor.fetchall()
        
        return stats

    @staticmethod
    def get_overdue_books(db: Database) -> List[Dict]:
        """获取超期未还的图书"""
        db.execute_query("""
            SELECT 
                b.id as borrowing_id,
                u.username,
                bk.title,
                b.borrow_date,
                DATEDIFF(CURRENT_DATE, b.borrow_date) as overdue_days
            FROM borrowings b
            JOIN users u ON b.user_id = u.id
            JOIN books bk ON b.book_id = bk.id
            WHERE b.return_date IS NULL 
            AND b.status = 'approved'
            AND DATEDIFF(CURRENT_DATE, b.borrow_date) > 30
            ORDER BY overdue_days DESC
        """)
        return db.cursor.fetchall() 