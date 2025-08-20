"""管理員路由"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..services.user_service import UserService
from ..services.leave_service import LeaveService
from ..exceptions import ValidationError, BusinessLogicError, DatabaseError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """管理員權限裝飾器"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理員權限', 'danger')
            return redirect(url_for('leave.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def admin():
    """管理員主頁"""
    try:
        users = UserService.get_all_non_admin_users()
        user_ids = [user.id for user in users]
        leave_records = LeaveService.get_recent_leave_records_by_users(user_ids, 5)
        
        return render_template('admin.html', users=users, leave_records=leave_records)
    except Exception as e:
        flash('載入管理頁面時發生錯誤', 'danger')
        return redirect(url_for('main.index'))


@admin_bp.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    """新增用戶"""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    try:
        UserService.create_user(username, password)
        flash('新增用戶成功！', 'success')
    except (ValidationError, BusinessLogicError) as e:
        flash(str(e), 'danger')
    except DatabaseError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('新增用戶時發生未知錯誤', 'danger')
    
    return redirect(url_for('admin.admin'))


@admin_bp.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    """更新用戶請假天數"""
    leave_days_data = {
        'annual_leave': request.form.get('annual_leave', 0),
        'sick_leave': request.form.get('sick_leave', 0),
        'personal_leave': request.form.get('personal_leave', 0),
        'menstrual_leave': request.form.get('menstrual_leave', 0),
        'family_care_leave': request.form.get('family_care_leave', 0),
        'compassionate_leave': request.form.get('compassionate_leave', 0)
    }
    
    try:
        UserService.update_user_leave_days(user_id, leave_days_data)
        flash('用戶天數更新成功', 'success')
    except (ValidationError, BusinessLogicError) as e:
        flash(str(e), 'danger')
    except DatabaseError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('更新用戶資料時發生未知錯誤', 'danger')
    
    return redirect(url_for('admin.admin'))


@admin_bp.route('/update_password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_password(user_id):
    """更新用戶密碼"""
    new_password = request.form.get('new_password', '')
    
    try:
        UserService.update_password(user_id, new_password)
        flash('密碼更新成功', 'success')
    except (ValidationError, BusinessLogicError) as e:
        flash(str(e), 'danger')
    except DatabaseError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('更新密碼時發生未知錯誤', 'danger')
    
    return redirect(url_for('leave.user_records', user_id=user_id))


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """刪除用戶"""
    try:
        UserService.delete_user(user_id)
        flash('用戶刪除成功', 'success')
    except (ValidationError, BusinessLogicError) as e:
        flash(str(e), 'danger')
    except DatabaseError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('刪除用戶時發生未知錯誤', 'danger')
    
    return redirect(url_for('admin.admin'))