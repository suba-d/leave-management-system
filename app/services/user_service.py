"""用戶管理服務"""
from flask import current_app
from sqlalchemy.exc import IntegrityError
from ..models import User, LeaveRecord, db
from ..exceptions import ValidationError, DatabaseError, BusinessLogicError


class UserService:
    """用戶管理服務類"""
    
    @staticmethod
    def create_user(username, password, leave_days_config=None):
        """創建新用戶"""
        if not username or not password:
            raise ValidationError("用戶名和密碼不能為空")
        
        username = username.lower().strip().capitalize()
        
        # 檢查用戶是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            raise BusinessLogicError(f"帳號 {username} 已存在")
        
        # 設置預設請假天數
        if leave_days_config is None:
            leave_days_config = current_app.config['DEFAULT_LEAVE_DAYS']
        
        new_user = User(
            username=username,
            password=password,
            vacation_days=leave_days_config['annual_leave'],
            sick_days=leave_days_config['sick_leave'],
            personal_days=leave_days_config['personal_leave'],
            menstrual_days=leave_days_config['menstrual_leave'],
            family_care_days=leave_days_config['family_care_leave'],
            compassionate_days=leave_days_config['compassionate_leave']
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.info(f"User {username} created successfully")
            return new_user
        except IntegrityError:
            db.session.rollback()
            raise DatabaseError(f"創建用戶 {username} 時發生資料庫錯誤")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user {username}: {e}")
            raise DatabaseError("創建用戶時發生未知錯誤")
    
    @staticmethod
    def update_user_leave_days(user_id, leave_days_data):
        """更新用戶請假天數"""
        user = User.query.get(user_id)
        if not user:
            raise BusinessLogicError("找不到該用戶")
        
        try:
            user.vacation_days = float(leave_days_data.get('annual_leave', 0))
            user.sick_days = float(leave_days_data.get('sick_leave', 0))
            user.personal_days = float(leave_days_data.get('personal_leave', 0))
            user.menstrual_days = float(leave_days_data.get('menstrual_leave', 0))
            user.family_care_days = float(leave_days_data.get('family_care_leave', 0))
            user.compassionate_days = float(leave_days_data.get('compassionate_leave', 0))
            
            db.session.commit()
            current_app.logger.info(f"Updated leave days for user {user.username}")
            return user
        except ValueError:
            raise ValidationError("請假天數必須為有效數字")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user {user_id}: {e}")
            raise DatabaseError("更新用戶資料時發生錯誤")
    
    @staticmethod
    def update_password(user_id, new_password):
        """更新用戶密碼"""
        user = User.query.get(user_id)
        if not user:
            raise BusinessLogicError("找不到該用戶")
        
        if not new_password:
            raise ValidationError("新密碼不能為空")
        
        try:
            user.password = new_password
            db.session.commit()
            current_app.logger.info(f"Password updated for user {user.username}")
            return user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating password for user {user_id}: {e}")
            raise DatabaseError("更新密碼時發生錯誤")
    
    @staticmethod
    def delete_user(user_id):
        """刪除用戶"""
        user = User.query.get(user_id)
        if not user:
            raise BusinessLogicError("找不到該用戶")
        
        if user.is_admin:
            raise BusinessLogicError("無法刪除管理員帳戶")
        
        try:
            username = user.username
            db.session.delete(user)
            db.session.commit()
            current_app.logger.info(f"User {username} deleted successfully")
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting user {user_id}: {e}")
            raise DatabaseError("刪除用戶時發生錯誤")
    
    @staticmethod
    def get_all_non_admin_users():
        """獲取所有非管理員用戶"""
        return User.query.filter_by(is_admin=False).all()
    
    @staticmethod
    def get_user_by_id(user_id):
        """根據ID獲取用戶"""
        return User.query.get(user_id)