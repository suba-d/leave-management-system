# 建立 User 模型
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    vacation_days = db.Column(db.Float, default=0.0)
    sick_days = db.Column(db.Float, default=0.0)
    personal_days = db.Column(db.Float, default=0.0)
    menstrual_days = db.Column(db.Float, default=0.0)
    family_care_days = db.Column(db.Float, default=0.0)
    compassionate_days = db.Column(db.Float, default=0.0)

# 建立 LeaveRecord 模型
class LeaveRecord(db.Model):
    __tablename__ = 'leave_record'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    leave_type = db.Column(db.String(50))  
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    half_day = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(255))
    receipt_url = db.Column(db.String(500))
    days = db.Column(db.Float, nullable=False)