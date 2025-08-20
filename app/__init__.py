from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
import os

from .config import Config
from .models import db, User
from .utils.logging_config import setup_logging
from .utils.error_handlers import register_error_handlers


def create_app(config_class=Config):
    """
    建立並配置 Flask 應用程式
    """
    # 設置模板和靜態文件路徑
    import os
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)
    
    # 設置日誌
    setup_logging(app)
    
    # 初始化擴展
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # 設置 LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 註冊錯誤處理器
    register_error_handlers(app)
    
    # 註冊藍圖
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.leave import leave_bp
    from .routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(main_bp)
    
    return app