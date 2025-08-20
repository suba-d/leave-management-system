"""資料驗證工具"""
import re
from datetime import datetime, date
from ..exceptions import ValidationError


class Validator:
    """資料驗證器"""
    
    @staticmethod
    def validate_username(username):
        """驗證用戶名"""
        if not username:
            raise ValidationError("用戶名不能為空")
        
        username = username.strip()
        if len(username) < 2:
            raise ValidationError("用戶名至少需要2個字符")
        
        if len(username) > 50:
            raise ValidationError("用戶名不能超過50個字符")
        
        # 檢查是否包含特殊字符
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fff_-]+$', username):
            raise ValidationError("用戶名只能包含字母、數字、中文、底線和連字符")
        
        return username.strip()
    
    @staticmethod
    def validate_password(password):
        """驗證密碼"""
        if not password:
            raise ValidationError("密碼不能為空")
        
        if len(password) < 4:
            raise ValidationError("密碼至少需要4個字符")
        
        if len(password) > 50:
            raise ValidationError("密碼不能超過50個字符")
        
        return password
    
    @staticmethod
    def validate_date_string(date_string, field_name="日期"):
        """驗證日期字串格式"""
        if not date_string:
            raise ValidationError(f"{field_name}不能為空")
        
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError(f"{field_name}格式錯誤，請使用 YYYY-MM-DD 格式")
    
    @staticmethod
    def validate_leave_type(leave_type):
        """驗證請假類型"""
        valid_types = ['特休', '病假', '事假', '生理假', '家庭照顧假', '同情假']
        if leave_type not in valid_types:
            raise ValidationError(f"無效的請假類型，可選類型：{', '.join(valid_types)}")
        return leave_type
    
    @staticmethod
    def validate_leave_days(days):
        """驗證請假天數"""
        try:
            days = float(days)
        except (ValueError, TypeError):
            raise ValidationError("請假天數必須為有效數字")
        
        if days <= 0:
            raise ValidationError("請假天數必須大於0")
        
        if days > 365:
            raise ValidationError("請假天數不能超過365天")
        
        return days
    
    @staticmethod
    def validate_email(email):
        """驗證電子郵件格式"""
        if not email:
            return email  # 允許空值
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("電子郵件格式不正確")
        
        return email.lower().strip()
    
    @staticmethod
    def validate_phone(phone):
        """驗證電話號碼格式"""
        if not phone:
            return phone  # 允許空值
        
        # 移除所有非數字字符
        clean_phone = re.sub(r'\D', '', phone)
        
        # 檢查長度（台灣手機號碼通常是10位數）
        if len(clean_phone) < 8 or len(clean_phone) > 15:
            raise ValidationError("電話號碼長度不正確")
        
        return clean_phone
    
    @staticmethod
    def validate_file_size(file_size, max_size=16*1024*1024):  # 預設16MB
        """驗證檔案大小"""
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise ValidationError(f"檔案大小不能超過 {max_mb:.1f}MB")
        
        return True
    
    @staticmethod
    def validate_file_extension(filename, allowed_extensions=None):
        """驗證檔案副檔名"""
        if allowed_extensions is None:
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx']
        
        if '.' not in filename:
            raise ValidationError("檔案必須有副檔名")
        
        extension = filename.rsplit('.', 1)[1].lower()
        if extension not in allowed_extensions:
            raise ValidationError(f"不支援的檔案格式，允許的格式：{', '.join(allowed_extensions)}")
        
        return extension