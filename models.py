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
    __tablename__ = 'leave_record'   # 可選，不寫的話預設表名會是 leave_record
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    leave_type = db.Column(db.String(50))  
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    half_day = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(255))  # 確保模型中定義了 reason 欄位
    receipt_url = db.Column(db.String(500))  # 新增收據URL字段
    days = db.Column(db.Float, nullable=False)  # 假設這個屬性表示請假天數