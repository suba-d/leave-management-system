"""身份驗證服務"""
from flask import current_app
from flask_login import login_user, logout_user
from ..models import User, db
from ..exceptions import AuthenticationError, ValidationError


class AuthService:
    """身份驗證服務類"""
    
    @staticmethod
    def authenticate_user(username, password):
        """驗證用戶身份"""
        if not username or not password:
            raise ValidationError("用戶名和密碼不能為空")
        
        # 統一用戶名格式（首字母大寫，與創建時一致）
        username = username.lower().strip().capitalize()
        password = password.lower().strip()
        
        user = User.query.filter_by(username=username).first()
        if not user or user.password.lower() != password:
            raise AuthenticationError("帳號或密碼錯誤")
        
        return user
    
    @staticmethod
    def login(username, password):
        """用戶登入"""
        user = AuthService.authenticate_user(username, password)
        login_user(user)
        current_app.logger.info(f"User {username} logged in successfully")
        return user
    
    @staticmethod
    def logout():
        """用戶登出"""
        logout_user()
        current_app.logger.info("User logged out")
    
    @staticmethod
    def is_admin(user):
        """檢查用戶是否為管理員"""
        return user and user.is_admin