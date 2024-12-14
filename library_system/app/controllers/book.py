from flask import Blueprint, request, render_template, jsonify
from flask_login import login_required
from ..models.book import Book
from ..models.db import Database

book = Blueprint('book', __name__)

@book.route('/books')
@login_required
def list_books():
    page = request.args.get('page', 1, type=int)
    db = Database()
    try:
        books = Book.get_all(db, page=page)
        return render_template('books/list.html', books=books)
    finally:
        db.close()

@book.route('/books/<int:book_id>')
@login_required
def get_book(book_id):
    db = Database()
    try:
        book = Book.get_by_id(db, book_id)
        if not book:
            return jsonify({'error': '图书不存在'}), 404
        return render_template('books/detail.html', book=book)
    finally:
        db.close() 