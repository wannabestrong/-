import matplotlib
matplotlib.use('Agg')  # 设置后端为Agg，这样不需要GUI环境
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from typing import List, Dict, Any
from .db import Database

class Statistics:
    @staticmethod
    def get_borrowing_trends(db: Database) -> Dict[str, Any]:
        """获取借阅趋势数据"""
        db.execute_query("""
            SELECT 
                DATE_FORMAT(borrow_date, '%Y-%m') as month,
                COUNT(*) as borrow_count,
                COUNT(DISTINCT user_id) as user_count,
                COUNT(DISTINCT book_id) as book_count
            FROM borrowings
            WHERE borrow_date >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(borrow_date, '%Y-%m')
            ORDER BY month
        """)
        return db.cursor.fetchall()

    @staticmethod
    def get_category_stats(db: Database) -> List[Dict]:
        """获取分类统计数据"""
        db.execute_query("""
            SELECT 
                c.name as category_name,
                COUNT(DISTINCT b.id) as book_count,
                COUNT(br.id) as borrow_count,
                ROUND(AVG(b.price), 2) as avg_price
            FROM categories c
            LEFT JOIN books b ON c.id = b.category_id
            LEFT JOIN borrowings br ON b.id = br.book_id
            GROUP BY c.id, c.name
            ORDER BY borrow_count DESC
        """)
        return db.cursor.fetchall()

    @staticmethod
    def get_user_activity(db: Database) -> Dict[str, Any]:
        """获取用户活动统计"""
        stats = {}
        
        # 用户借阅频率分布
        db.execute_query("""
            SELECT 
                CASE 
                    WHEN borrow_count >= 20 THEN '频繁借阅(>=20)'
                    WHEN borrow_count >= 10 THEN '中度借阅(10-19)'
                    WHEN borrow_count >= 5 THEN '一般借阅(5-9)'
                    ELSE '偶尔借阅(<5)'
                END as user_type,
                COUNT(*) as user_count
            FROM (
                SELECT user_id, COUNT(*) as borrow_count
                FROM borrowings
                GROUP BY user_id
            ) user_stats
            GROUP BY user_type
            ORDER BY user_count DESC
        """)
        stats['user_types'] = db.cursor.fetchall()
        
        # 借阅时长分布
        db.execute_query("""
            SELECT 
                CASE 
                    WHEN days <= 7 THEN '一周内'
                    WHEN days <= 14 THEN '两周内'
                    WHEN days <= 30 THEN '一个月内'
                    ELSE '超过一个月'
                END as duration,
                COUNT(*) as count
            FROM (
                SELECT DATEDIFF(IFNULL(return_date, CURRENT_DATE), borrow_date) as days
                FROM borrowings
                WHERE return_date IS NOT NULL
            ) duration_stats
            GROUP BY duration
            ORDER BY count DESC
        """)
        stats['duration_dist'] = db.cursor.fetchall()
        
        return stats

    @staticmethod
    def generate_charts(data: Dict[str, Any]) -> Dict[str, str]:
        """生成统计图表"""
        charts = {}
        
        # 借阅趋势图
        plt.figure(figsize=(12, 6))
        df = pd.DataFrame(data['borrowing_trends'])
        plt.plot(df['month'], df['borrow_count'], marker='o', label='借阅量')
        plt.plot(df['month'], df['user_count'], marker='s', label='借阅人数')
        plt.title('月度借阅趋势')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True)
        
        # 将图表转换为base64字符串
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        charts['trends'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # 分类统计饼图
        plt.figure(figsize=(10, 10))
        df = pd.DataFrame(data['category_stats'])
        plt.pie(df['borrow_count'], labels=df['category_name'], autopct='%1.1f%%')
        plt.title('各分类借阅比例')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        charts['categories'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return charts 