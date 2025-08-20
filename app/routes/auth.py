"""身份驗證路由"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..services.auth_service import AuthService
from ..exceptions import AuthenticationError, ValidationError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登入頁面"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        try:
            user = AuthService.login(username, password)
            return redirect(url_for('admin.admin' if user.is_admin else 'leave.dashboard'))
        except (AuthenticationError, ValidationError) as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('登入時發生未知錯誤', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """登出"""
    AuthService.logout()
    flash('已成功登出', 'info')
    return redirect(url_for('auth.login'))