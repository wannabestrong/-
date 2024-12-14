-- 创建借阅统计视图
CREATE OR REPLACE VIEW vw_borrowing_stats AS
SELECT 
    b.book_id,
    books.title,
    books.author,
    COUNT(*) as borrow_count,
    COUNT(CASE WHEN b.return_date IS NULL THEN 1 END) as current_borrowed
FROM borrowings b
JOIN books ON b.book_id = books.id
GROUP BY b.book_id, books.title, books.author;

-- 创建用户借阅历史视图
CREATE OR REPLACE VIEW vw_user_borrowing_history AS
SELECT 
    u.username,
    b.book_id,
    books.title,
    b.borrow_date,
    b.return_date,
    DATEDIFF(IFNULL(b.return_date, CURRENT_DATE), b.borrow_date) as borrow_days
FROM borrowings b
JOIN users u ON b.user_id = u.id
JOIN books ON b.book_id = books.id;

-- 创建图书库存预警视图
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
HAVING available_stock < 5; 