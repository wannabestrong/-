DELIMITER //

-- 借书时检查库存触发器
CREATE TRIGGER tr_check_stock_before_borrow
BEFORE INSERT ON borrowings
FOR EACH ROW
BEGIN
    DECLARE v_stock INT;
    DECLARE v_borrowed INT;
    
    SELECT stock INTO v_stock 
    FROM books 
    WHERE id = NEW.book_id;
    
    SELECT COUNT(*) INTO v_borrowed 
    FROM borrowings 
    WHERE book_id = NEW.book_id 
    AND return_date IS NULL;
    
    IF v_stock - v_borrowed <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '库存不足';
    END IF;
END //

-- 更新图书时记录日志触发器
CREATE TRIGGER tr_book_update_log
AFTER UPDATE ON books
FOR EACH ROW
BEGIN
    INSERT INTO book_update_logs (
        book_id,
        field_name,
        old_value,
        new_value,
        update_time
    )
    SELECT 
        NEW.id,
        CASE 
            WHEN NEW.title != OLD.title THEN 'title'
            WHEN NEW.price != OLD.price THEN 'price'
            WHEN NEW.stock != OLD.stock THEN 'stock'
        END,
        CASE 
            WHEN NEW.title != OLD.title THEN OLD.title
            WHEN NEW.price != OLD.price THEN OLD.price
            WHEN NEW.stock != OLD.stock THEN OLD.stock
        END,
        CASE 
            WHEN NEW.title != OLD.title THEN NEW.title
            WHEN NEW.price != OLD.price THEN NEW.price
            WHEN NEW.stock != OLD.stock THEN NEW.stock
        END,
        NOW();
END //

DELIMITER ; 