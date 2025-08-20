"""請假記錄模型"""
from sqlalchemy import Index
from . import db


class LeaveRecord(db.Model):
    """請假記錄模型"""
    __tablename__ = 'leave_record'
    __table_args__ = (
        Index('idx_leave_user_date', 'user_id', 'start_date'),
        Index('idx_leave_date_range', 'start_date', 'end_date'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    half_day = db.Column(db.Boolean, default=False, nullable=False)
    reason = db.Column(db.String(255))
    receipt_url = db.Column(db.String(500))
    days = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<LeaveRecord {self.user_id}: {self.leave_type} {self.days} days>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'half_day': self.half_day,
            'reason': self.reason,
            'receipt_url': self.receipt_url,
            'days': self.days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_user_and_year(cls, user_id, year):
        """獲取指定用戶和年份的請假記錄"""
        return cls.query.filter(
            cls.user_id == user_id,
            db.extract('year', cls.start_date) == year
        ).all()
    
    @classmethod
    def get_recent_by_user(cls, user_id, limit=5):
        """獲取用戶最近的請假記錄"""
        return cls.query.filter_by(user_id=user_id)\
                      .order_by(cls.start_date.desc())\
                      .limit(limit)\
                      .all()