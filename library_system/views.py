from app.models.db import Database

def create_views():
    db = Database()
    try:
        # 创建图书库存预警视图
        db.execute_query("""
            CREATE OR REPLACE VIEW vw_book_stock_alert AS
            SELECT 
                b.id,
                b.title,
                b.stock,
                COUNT(br.id) as borrowed_count,
                b.stock - COUNT(CASE WHEN br.return_date IS NULL THEN 1 END) as available_stock
            FROM books b
            LEFT JOIN borrowings br ON b.id = br.book_id AND br.return_date IS NULL
            GROUP BY b.id, b.title, b.stock
            HAVING available_stock < 5
        """)
        print("视图创建成功！")
    except Exception as e:
        print(f"错误：{e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_views()
