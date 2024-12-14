import csv
import io
from turtle import pd
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

from app.models.statistics import Statistics
from app.models.system import DatabaseBackup, SystemLog
from ..models.db import Database
from ..models.book import Book
from ..models.user import User
from ..models.borrowing import Borrowing
from functools import wraps

admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.username != 'admin':
            flash('需要管理员权限')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

# 用户管理路由
@admin.route('/users')
@login_required
@admin_required
def list_users():
    db = Database()
    try:
        db.execute_query("SELECT * FROM users")
        users = db.cursor.fetchall()
        return render_template('admin/users.html', users=users)
    finally:
        db.close()

@admin.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    db = Database()
    try:
        User.create(
            db,
            username=request.form['username'],
            password=request.form['password'],
            email=request.form['email']
        )
        db.commit()
        flash('用户添加成功')
    except Exception as e:
        db.rollback()
        flash(f'添加失败：{str(e)}')
    finally:
        db.close()
    return redirect(url_for('admin.list_users'))

@admin.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    db = Database()
    try:
        db.execute_query("DELETE FROM users WHERE id = %s AND username != 'admin'", (user_id,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db.close()

# 图书管理路由
@admin.route('/books')
@login_required
@admin_required
def list_books():
    db = Database()
    try:
        db.execute_query("SELECT * FROM books")
        books = db.cursor.fetchall()
        return render_template('admin/books.html', books=books)
    finally:
        db.close()

@admin.route('/books/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_book():
    db = Database()
    try:
        books = Book.get_all(db)
        
        if request.method == 'POST':
            Book.create(
                db,
                title=request.form['title'],
                isbn=request.form['isbn'],
                publisher_id=request.form['publisher_id'],
                category_id=request.form['category_id']
            )
            flash('图书添加成功')
            return redirect(url_for('admin.list_books'))
        
        return render_template('admin/add_book.html', books=books)
    except Exception as e:
        flash(f'操作失败：{str(e)}')
        return redirect(url_for('admin.list_books'))
    finally:
        db.close()

@admin.route('/books/<int:book_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_book(book_id):
    db = Database()
    try:
        db.execute_query("DELETE FROM books WHERE id = %s", (book_id,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db.close() 

@admin.route('/books/batch', methods=['POST'])
@login_required
@admin_required
def batch_manage_books():
    db = Database()
    try:
        action = request.form.get('action')
        book_ids = request.form.getlist('book_ids[]')
        
        if not book_ids:
            return jsonify({'error': '未选择图书'}), 400
            
        if action == 'delete':
            Book.batch_delete(db, book_ids)
            flash('批量删除成功')
        elif action == 'update_stock':
            stock_changes = []
            for book_id in book_ids:
                change = request.form.get(f'stock_change_{book_id}')
                if change:
                    stock_changes.append({
                        'book_id': book_id,
                        'change': int(change)
                    })
            Book.batch_update_stock(db, stock_changes)
            flash('库存更新成功')
            
        return redirect(url_for('admin.list_books'))
    except Exception as e:
        flash(f'操作失败：{str(e)}')
        return redirect(url_for('admin.list_books'))
    finally:
        db.close()

@admin.route('/books/stock-alert')
@login_required
@admin_required
def stock_alert():
    db = Database()
    try:
        alerts = Book.get_stock_alerts(db)
        return render_template('admin/stock_alert.html', alerts=alerts)
    finally:
        db.close()

@admin.route('/books/<int:book_id>', methods=['PUT'])
@login_required
@admin_required
def update_book(book_id):
    db = Database()
    try:
        data = request.get_json()
        updates = {}
        for field in ['title', 'author', 'isbn', 'price', 'stock']:
            if field in data:
                updates[field] = data[field]
                
        if not updates:
            return jsonify({'error': '无效的更新数据'}), 400
            
        Book.update_with_log(db, book_id, updates)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close() 

@admin.route('/borrowings')
@login_required
@admin_required
def manage_borrowings():
    db = Database()
    try:
        pending = Borrowing.get_pending_approvals(db)
        overdue = Borrowing.get_overdue_books(db)
        stats = Borrowing.get_statistics(db)
        return render_template('admin/borrowings.html',
                             pending=pending,
                             overdue=overdue,
                             stats=stats)
    finally:
        db.close()

@admin.route('/borrowings/<int:borrowing_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_borrowing(borrowing_id):
    db = Database()
    try:
        approved = request.form.get('approved') == 'true'
        Borrowing.approve(db, borrowing_id, approved)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@admin.route('/borrowings/export')
@login_required
@admin_required
def export_borrowings():
    db = Database()
    try:
        # 获取导出时间范围
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        db.execute_query("""
            SELECT 
                b.id,
                u.username,
                bk.title,
                b.borrow_date,
                b.return_date,
                b.status,
                DATEDIFF(IFNULL(b.return_date, CURRENT_DATE), b.borrow_date) as days
            FROM borrowings b
            JOIN users u ON b.user_id = u.id
            JOIN books bk ON b.book_id = bk.id
            WHERE b.borrow_date BETWEEN %s AND %s
            ORDER BY b.borrow_date DESC
        """, (start_date, end_date))
        
        records = db.cursor.fetchall()
        
        # 生成CSV文件
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '用户名', '图书', '借阅日期', '归还日期', '状态', '借阅天数'])
        
        for record in records:
            writer.writerow([
                record['id'],
                record['username'],
                record['title'],
                record['borrow_date'],
                record['return_date'] or '未归还',
                record['status'],
                record['days']
            ])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=borrowings.csv'
            }
        )
    finally:
        db.close()

@admin.route('/system')
@login_required
@admin_required
def system_management():
    db = Database()
    try:
        # 获取系统日志
        logs = SystemLog.get_logs(db, limit=50)
        # 获取备份列表
        backups = DatabaseBackup.list_backups()
        
        return render_template('admin/system.html',
                             logs=logs,
                             backups=backups)
    finally:
        db.close()

@admin.route('/system/backup', methods=['POST'])
@login_required
@admin_required
def create_backup():
    db = Database()
    try:
        filename = DatabaseBackup.create_backup(db)
        SystemLog.log_operation(db, current_user.id, 'create_backup', 
                              f'Created backup: {filename}')
        flash('备份创建成功')
        return redirect(url_for('admin.system_management'))
    except Exception as e:
        flash(f'备份失败：{str(e)}')
        return redirect(url_for('admin.system_management'))
    finally:
        db.close()

@admin.route('/system/restore/<filename>', methods=['POST'])
@login_required
@admin_required
def restore_backup(filename):
    db = Database()
    try:
        DatabaseBackup.restore_backup(db, filename)
        SystemLog.log_operation(db, current_user.id, 'restore_backup',
                              f'Restored from backup: {filename}')
        flash('数据恢复成功')
        return redirect(url_for('admin.system_management'))
    except Exception as e:
        flash(f'恢复失败：{str(e)}')
        return redirect(url_for('admin.system_management'))
    finally:
        db.close()

@admin.route('/logs')
@login_required
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    operation_type = request.args.get('operation_type')
    
    db = Database()
    try:
        logs_data = SystemLog.get_logs(
            db, 
            page=page,
            start_date=start_date,
            end_date=end_date,
            operation_type=operation_type
        )
        return render_template(
            'admin/logs.html',
            logs=logs_data['items'],
            total_pages=logs_data['total_pages'],
            current_page=page
        )
    finally:
        db.close()

@admin.route('/reports')
@login_required
@admin_required
def view_reports():
    db = Database()
    try:
        # 获取统计数据
        borrowing_trends = Statistics.get_borrowing_trends(db)
        category_stats = Statistics.get_category_stats(db)
        user_activity = Statistics.get_user_activity(db)
        
        # 生成图表
        charts = Statistics.generate_charts({
            'borrowing_trends': borrowing_trends,
            'category_stats': category_stats
        })
        
        return render_template('admin/reports.html',
                             borrowing_trends=borrowing_trends,
                             category_stats=category_stats,
                             user_activity=user_activity,
                             charts=charts)
    finally:
        db.close()

@admin.route('/reports/export')
@login_required
@admin_required
def export_report():
    db = Database()
    try:
        report_type = request.args.get('type')
        format = request.args.get('format', 'csv')
        
        if report_type == 'borrowing_trends':
            data = Statistics.get_borrowing_trends(db)
        elif report_type == 'category_stats':
            data = Statistics.get_category_stats(db)
        elif report_type == 'user_activity':
            data = Statistics.get_user_activity(db)
        else:
            return jsonify({'error': '无效的报表类型'}), 400
            
        if format == 'csv':
            # 导出CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(data[0].keys())
            # 写入数据
            for row in data:
                writer.writerow(row.values())
                
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename={report_type}.csv'
                }
            )
        elif format == 'excel':
            # 导出Excel
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)
                
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={
                    'Content-Disposition': f'attachment; filename={report_type}.xlsx'
                }
            )
        else:
            return jsonify({'error': '不支持的导出格式'}), 400
            
    finally:
        db.close()