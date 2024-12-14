DELIMITER //

-- 借书存储过程
CREATE PROCEDURE sp_borrow_book(
    IN p_user_id INT,
    IN p_book_id INT,
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(100)
)
BEGIN
    DECLARE v_stock INT;
    DECLARE v_borrowed INT;
    
    START TRANSACTION;
    
    -- 检查库存
    SELECT stock INTO v_stock FROM books WHERE id = p_book_id FOR UPDATE;
    SELECT COUNT(*) INTO v_borrowed 
    FROM borrowings 
    WHERE book_id = p_book_id AND return_date IS NULL;
    
    IF v_stock - v_borrowed <= 0 THEN
        SET p_success = FALSE;
        SET p_message = '库存不足';
        ROLLBACK;
    ELSE
        -- 插入借阅记录
        INSERT INTO borrowings (user_id, book_id, borrow_date)
        VALUES (p_user_id, p_book_id, CURRENT_DATE);
        
        SET p_success = TRUE;
        SET p_message = '借阅成功';
        COMMIT;
    END IF;
END //

-- 还书存储过程
CREATE PROCEDURE sp_return_book(
    IN p_user_id INT,
    IN p_book_id INT,
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(100)
)
BEGIN
    START TRANSACTION;
    
    UPDATE borrowings 
    SET return_date = CURRENT_DATE
    WHERE user_id = p_user_id 
    AND book_id = p_book_id 
    AND return_date IS NULL;
    
    IF ROW_COUNT() > 0 THEN
        SET p_success = TRUE;
        SET p_message = '还书成功';
        COMMIT;
    ELSE
        SET p_success = FALSE;
        SET p_message = '未找到相关借阅记录';
        ROLLBACK;
    END IF;
END //

DELIMITER ; 