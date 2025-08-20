"""自定義異常類"""


class LeaveSystemException(Exception):
    """請假系統基礎異常類"""
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(LeaveSystemException):
    """資料驗證錯誤"""
    pass


class BusinessLogicError(LeaveSystemException):
    """業務邏輯錯誤"""
    pass


class DatabaseError(LeaveSystemException):
    """資料庫操作錯誤"""
    pass


class ExternalServiceError(LeaveSystemException):
    """外部服務錯誤"""
    pass


class AuthenticationError(LeaveSystemException):
    """身份驗證錯誤"""
    pass


class AuthorizationError(LeaveSystemException):
    """權限錯誤"""
    pass


class FileUploadError(LeaveSystemException):
    """檔案上傳錯誤"""
    pass