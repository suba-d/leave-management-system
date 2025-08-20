"""用戶模型"""
from flask_login import UserMixin
from sqlalchemy import Index
from . import db


class User(db.Model, UserMixin):
    """用戶模型"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # 請假天數欄位
    vacation_days = db.Column(db.Float, default=0.0, nullable=False)
    sick_days = db.Column(db.Float, default=0.0, nullable=False)
    personal_days = db.Column(db.Float, default=0.0, nullable=False)
    menstrual_days = db.Column(db.Float, default=0.0, nullable=False)
    family_care_days = db.Column(db.Float, default=0.0, nullable=False)
    compassionate_days = db.Column(db.Float, default=0.0, nullable=False)
    
    # 建立與請假記錄的關聯
    leave_records = db.relationship('LeaveRecord', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_remaining_days(self, leave_type_field):
        """獲取指定請假類型的剩餘天數"""
        return getattr(self, leave_type_field, 0.0)
    
    def deduct_leave_days(self, leave_type_field, days):
        """扣除請假天數"""
        current_days = getattr(self, leave_type_field, 0.0)
        setattr(self, leave_type_field, current_days - days)
    
    def restore_leave_days(self, leave_type_field, days):
        """恢復請假天數（用於刪除請假記錄時）"""
        current_days = getattr(self, leave_type_field, 0.0)
        setattr(self, leave_type_field, current_days + days)
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'vacation_days': self.vacation_days,
            'sick_days': self.sick_days,
            'personal_days': self.personal_days,
            'menstrual_days': self.menstrual_days,
            'family_care_days': self.family_care_days,
            'compassionate_days': self.compassionate_days
        }


# 創建索引
Index('idx_user_username', User.username)