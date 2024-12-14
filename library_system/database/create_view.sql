CREATE VIEW vw_book_stock_alert AS
SELECT 
    b.book_id,
    b.title,
    b.author,
    b.isbn,
    b.total_copies,
    (b.total_copies - COALESCE(
        (SELECT COUNT(*) 
         FROM borrowing_records br 
         WHERE br.book_id = b.book_id 
         AND br.return_date IS NULL), 0
    )) as available_copies
FROM 
    books b
HAVING available_copies <= 2; 