from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from .controllers.admin import admin

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        from .models.db import Database
        db = Database()
        try:
            return User.get_by_id(db, int(user_id))
        finally:
            db.close()
    
    @app.route('/')
    def index():
        return render_template("index.html")
    
    from .controllers.auth import auth
    from .controllers.book import book
    from .controllers.borrowing import borrowing
    
    app.register_blueprint(auth)
    app.register_blueprint(book)
    app.register_blueprint(borrowing)
    app.register_blueprint(admin)
    
    return app 