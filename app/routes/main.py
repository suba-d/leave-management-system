"""主要路由"""
from flask import Blueprint, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首頁路由"""
    if current_user.is_authenticated:
        # 如果是管理員，就進 admin；否則 base
        return redirect(url_for('admin.admin' if current_user.is_admin else 'main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
def dashboard():
    """用戶儀表板"""
    return redirect(url_for('leave.dashboard'))