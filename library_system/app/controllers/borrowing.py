from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from ..models.db import Database
from datetime import datetime, timedelta

borrowing = Blueprint('borrowing', __name__)

@borrowing.route('/my-borrowings')
@login_required
def list_borrowings():
    db = Database()
    try:
        db.execute_query("""
            SELECT b.*, books.title as book_title
            FROM borrowings b
            JOIN books ON b.book_id = books.id
            WHERE b.user_id = %s
            ORDER BY b.borrow_date DESC
        """, (current_user.id,))
        borrowings = db.cursor.fetchall()
        return render_template('borrowings/list.html', borrowings=borrowings)
    finally:
        db.close()

@borrowing.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    db = Database()
    try:
        # 检查是否已借阅
        db.execute_query("""
            SELECT COUNT(*) as count FROM borrowings 
            WHERE user_id = %s AND book_id = %s AND return_date IS NULL
        """, (current_user.id, book_id))
        result = db.cursor.fetchone()
        if result['count'] > 0:
            return jsonify({"error": "你已经借阅了这本书"}), 400
            
        # 创建借阅记录
        db.execute_query("""
            INSERT INTO borrowings (user_id, book_id, borrow_date)
            VALUES (%s, %s, CURRENT_DATE)
        """, (current_user.id, book_id))
        
        db.commit()
        return jsonify({"message": "借阅成功"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@borrowing.route('/return/<int:borrowing_id>', methods=['POST'])
@login_required
def return_book(borrowing_id):
    db = Database()
    try:
        db.execute_query("""
            UPDATE borrowings 
            SET return_date = CURRENT_DATE
            WHERE id = %s AND user_id = %s
        """, (borrowing_id, current_user.id))
        
        if db.cursor.rowcount == 0:
            return jsonify({"error": "未找到借阅记录"}), 404
            
        db.commit()
        return jsonify({"message": "归还成功"}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close() 