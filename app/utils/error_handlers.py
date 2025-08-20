"""錯誤處理器"""
from flask import current_app, flash, redirect, url_for, request, jsonify
from ..exceptions import (
    ValidationError, 
    BusinessLogicError, 
    DatabaseError, 
    ExternalServiceError,
    AuthenticationError,
    AuthorizationError,
    FileUploadError
)


def register_error_handlers(app):
    """註冊錯誤處理器"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        current_app.logger.warning(f"Validation error: {error.message}")
        if request.is_json:
            return jsonify({'error': error.message, 'code': 'VALIDATION_ERROR'}), 400
        flash(error.message, 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(error):
        current_app.logger.warning(f"Business logic error: {error.message}")
        if request.is_json:
            return jsonify({'error': error.message, 'code': 'BUSINESS_ERROR'}), 400
        flash(error.message, 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        current_app.logger.error(f"Database error: {error.message}")
        if request.is_json:
            return jsonify({'error': '資料庫操作失敗', 'code': 'DATABASE_ERROR'}), 500
        flash('資料庫操作失敗，請稍後再試', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    @app.errorhandler(ExternalServiceError)
    def handle_external_service_error(error):
        current_app.logger.error(f"External service error: {error.message}")
        if request.is_json:
            return jsonify({'error': error.message, 'code': 'EXTERNAL_SERVICE_ERROR'}), 503
        flash(error.message, 'warning')
        return redirect(request.referrer or url_for('main.index'))
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        current_app.logger.warning(f"Authentication error: {error.message}")
        if request.is_json:
            return jsonify({'error': error.message, 'code': 'AUTH_ERROR'}), 401
        flash(error.message, 'danger')
        return redirect(url_for('auth.login'))
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        current_app.logger.warning(f"Authorization error: {error.message}")
        if request.is_json:
            return jsonify({'error': error.message, 'code': 'AUTHORIZATION_ERROR'}), 403
        flash(error.message, 'danger')
        return redirect(url_for('main.index'))
    
    @app.errorhandler(FileUploadError)
    def handle_file_upload_error(error):
        current_app.logger.error(f"File upload error: {error.message}")
        if request.is_json:
            return jsonify({'error': error.message, 'code': 'FILE_UPLOAD_ERROR'}), 400
        flash(error.message, 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    @app.errorhandler(404)
    def handle_not_found(error):
        current_app.logger.warning(f"404 error: {request.url}")
        if request.is_json:
            return jsonify({'error': '頁面不存在', 'code': 'NOT_FOUND'}), 404
        flash('頁面不存在', 'warning')
        return redirect(url_for('main.index'))
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        current_app.logger.error(f"500 error: {str(error)}")
        if request.is_json:
            return jsonify({'error': '內部伺服器錯誤', 'code': 'INTERNAL_ERROR'}), 500
        flash('系統發生錯誤，請稍後再試', 'danger')
        return redirect(url_for('main.index'))
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        current_app.logger.warning(f"403 error: {request.url}")
        if request.is_json:
            return jsonify({'error': '權限不足', 'code': 'FORBIDDEN'}), 403
        flash('權限不足', 'danger')
        return redirect(url_for('main.index'))