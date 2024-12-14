from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..models.user import User
from ..models.db import Database
from ..models.system import SystemLog

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: username={username}")
        
        db = Database()
        try:
            user = User.get_by_username(db, username)
            if user and user.check_password(password):
                login_user(user)
                SystemLog.add_log(
                    db,
                    user.id,
                    'login',
                    f'用户 {username} 登录成功',
                    request.remote_addr
                )
                print("Login successful")
                return redirect(url_for('index'))
            print("Login failed")
            flash('用户名或密码错误')
        finally:
            db.close()
            
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index')) 