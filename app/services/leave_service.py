"""請假管理服務"""
from datetime import datetime, timedelta
from flask import current_app
from ..models import LeaveRecord, User, db
from ..exceptions import ValidationError, BusinessLogicError, DatabaseError


class LeaveService:
    """請假管理服務類"""
    
    @staticmethod
    def calculate_leave_days(start_date, end_date, is_half_day=False):
        """計算請假天數"""
        if end_date < start_date:
            raise ValidationError("結束日期必須大於或等於開始日期")
        
        total_days = (end_date - start_date).days + 1
        
        # 單日範圍且勾選半天
        if total_days == 1:
            return 0.5 if is_half_day else 1.0
        
        # 多日範圍，若勾選半天，就扣 0.5
        leave_days = total_days
        if is_half_day:
            leave_days -= 0.5
        return leave_days
    
    @staticmethod
    def validate_leave_request(start_date, end_date, days, leave_type, user):
        """驗證請假申請"""
        config = current_app.config
        
        # 檢查開始日期不能比結束日期晚
        if start_date > end_date:
            raise ValidationError('開始日期不能比結束日期晚')
        
        # 檢查未來日期限制
        max_allowed_date = (datetime.now() + timedelta(days=config['MAX_FUTURE_DAYS'])).date()
        if start_date > max_allowed_date or end_date > max_allowed_date:
            raise ValidationError(f'請假日期不可超過 {config["MAX_FUTURE_DAYS"]} 天')
        
        # 檢查單次請假天數限制
        if days > config['MAX_LEAVE_DAYS']:
            raise ValidationError(f'單次請假天數不可超過 {config["MAX_LEAVE_DAYS"]} 天')
        
        # 檢查剩餘天數是否足夠
        leave_type_mapping = config['LEAVE_TYPE_MAPPING']
        if leave_type in leave_type_mapping:
            field_name = leave_type_mapping[leave_type]
            remaining_days = user.get_remaining_days(field_name)
            if days > remaining_days:
                raise ValidationError(f'{leave_type} 剩餘天數不足')
        else:
            raise ValidationError('未知的請假類型')
    
    @staticmethod
    def create_leave_request(user, leave_data):
        """創建請假申請"""
        start_date = datetime.strptime(leave_data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(leave_data['end_date'], '%Y-%m-%d').date()
        leave_type = leave_data['leave_type']
        half_day = leave_data.get('half_day', False)
        reason = leave_data.get('reason', '').strip()
        receipt_url = leave_data.get('receipt_url')
        
        # 處理半天假備註
        if half_day:
            if not reason:
                reason = "半天"
            elif not reason.startswith("半天"):
                reason = f"半天 - {reason}"
        
        # 計算請假天數
        days = LeaveService.calculate_leave_days(start_date, end_date, half_day)
        
        # 驗證請假申請
        LeaveService.validate_leave_request(start_date, end_date, days, leave_type, user)
        
        try:
            # 扣除用戶請假天數
            leave_type_mapping = current_app.config['LEAVE_TYPE_MAPPING']
            field_name = leave_type_mapping[leave_type]
            user.deduct_leave_days(field_name, days)
            
            # 創建請假記錄
            leave_record = LeaveRecord(
                user_id=user.id,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                half_day=half_day,
                reason=reason,
                receipt_url=receipt_url,
                days=days
            )
            
            db.session.add(leave_record)
            db.session.commit()
            
            current_app.logger.info(f"Leave request created for user {user.username}: {leave_type} {days} days")
            return leave_record
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating leave request: {e}")
            raise DatabaseError('請假申請失敗，請稍後再試')
    
    @staticmethod
    def delete_leave_record(leave_id, restore_days=True):
        """刪除請假記錄"""
        leave_record = LeaveRecord.query.get(leave_id)
        if not leave_record:
            raise BusinessLogicError("找不到該請假記錄")
        
        try:
            # 如果需要恢復天數
            if restore_days:
                user = leave_record.user
                leave_type_mapping = current_app.config['LEAVE_TYPE_MAPPING']
                field_name = leave_type_mapping[leave_record.leave_type]
                user.restore_leave_days(field_name, leave_record.days)
            
            user_id = leave_record.user_id
            db.session.delete(leave_record)
            db.session.commit()
            
            current_app.logger.info(f"Leave record {leave_id} deleted")
            return user_id
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting leave record {leave_id}: {e}")
            raise DatabaseError("刪除請假記錄時發生錯誤")
    
    @staticmethod
    def calculate_annual_leave_stats(leave_records, current_year):
        """計算年度請假統計"""
        stats = {
            'annual_leave_days': 0,
            'sick_leave_days': 0,
            'personal_leave_days': 0,
            'menstrual_leave_days': 0,
            'family_care_leave_days': 0,
            'compassionate_leave_days': 0
        }
        
        for record in leave_records:
            if record.start_date.year == current_year:
                if record.leave_type == '特休':
                    stats['annual_leave_days'] += record.days
                elif record.leave_type == '病假':
                    stats['sick_leave_days'] += record.days
                elif record.leave_type == '事假':
                    stats['personal_leave_days'] += record.days
                elif record.leave_type == '生理假':
                    stats['menstrual_leave_days'] += record.days
                elif record.leave_type == '家庭照顧假':
                    stats['family_care_leave_days'] += record.days
                elif record.leave_type == '同情假':
                    stats['compassionate_leave_days'] += record.days
        
        return stats
    
    @staticmethod
    def get_user_leave_records(user_id):
        """獲取用戶所有請假記錄"""
        return LeaveRecord.query.filter_by(user_id=user_id).order_by(LeaveRecord.start_date.desc()).all()
    
    @staticmethod
    def get_recent_leave_records_by_users(user_ids, limit=5):
        """獲取多個用戶的最近請假記錄"""
        records = {}
        for user_id in user_ids:
            records[user_id] = LeaveRecord.get_recent_by_user(user_id, limit)
        return records