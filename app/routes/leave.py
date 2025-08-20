"""請假相關路由"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..services.leave_service import LeaveService
from ..services.user_service import UserService
from ..services.google_service import get_google_service
from ..exceptions import ValidationError, BusinessLogicError, DatabaseError, ExternalServiceError

leave_bp = Blueprint('leave', __name__, url_prefix='/leave')


@leave_bp.route('/dashboard')
@login_required
def dashboard():
    """用戶儀表板（原 base 頁面）"""
    try:
        # 取得當前使用者請假紀錄
        leave_records = LeaveService.get_user_leave_records(current_user.id)
        
        # 計算年度請假統計
        current_year = datetime.now().year
        stats = LeaveService.calculate_annual_leave_stats(leave_records, current_year)
        
        return render_template(
            'base.html',
            username=current_user.username,
            vacation_days=current_user.vacation_days,
            sick_days=current_user.sick_days,
            personal_days=current_user.personal_days,
            menstrual_days=current_user.menstrual_days,
            family_care_days=current_user.family_care_days,
            compassionate_days=current_user.compassionate_days,
            leave_records=leave_records,
            current_year=current_year,
            **stats
        )
    except Exception as e:
        flash('載入儀表板時發生錯誤', 'danger')
        return redirect(url_for('auth.login'))


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    """申請請假"""
    if request.method == 'POST':
        leave_data = {
            'leave_type': request.form.get('leave_type'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'half_day': 'half_day' in request.form,
            'reason': request.form.get('reason', '').strip()
        }
        
        try:
            # 處理收據上傳
            receipt = request.files.get('receipt')
            if receipt and receipt.filename:
                google_service = get_google_service()
                receipt_url = google_service.process_receipt_upload(receipt)
                leave_data['receipt_url'] = receipt_url
            
            # 創建請假申請
            leave_record = LeaveService.create_leave_request(current_user, leave_data)
            flash('請假申請成功', 'success')
            
            # 嘗試同步到 Google Calendar
            try:
                google_service = get_google_service()
                event_summary = f"{current_user.username} - {leave_data['leave_type']}"
                calendar_event = google_service.create_calendar_event(
                    event_summary, 
                    leave_record.start_date, 
                    leave_record.end_date
                )
                if calendar_event:
                    flash('請假已同步至 Google 日曆', 'success')
                else:
                    flash('請假同步 Google 日曆失敗', 'warning')
            except ExternalServiceError:
                flash('請假同步 Google 日曆失敗', 'warning')
            
            return redirect(url_for('leave.apply'))
            
        except (ValidationError, BusinessLogicError) as e:
            flash(str(e), 'danger')
        except DatabaseError as e:
            flash(str(e), 'danger')
        except ExternalServiceError as e:
            flash(str(e), 'warning')
        except Exception as e:
            flash('請假申請時發生未知錯誤', 'danger')
    
    return render_template('leave.html', username=current_user.username)


@leave_bp.route('/user_records/<int:user_id>')
@login_required
def user_records(user_id):
    """查看用戶請假記錄"""
    # 檢查權限：管理員可以查看所有用戶，一般用戶只能查看自己的記錄
    if not current_user.is_admin and current_user.id != user_id:
        flash('無權限查看此用戶記錄', 'danger')
        return redirect(url_for('leave.dashboard'))
    
    try:
        user = UserService.get_user_by_id(user_id)
        if not user:
            flash('找不到該用戶', 'danger')
            return redirect(url_for('admin.admin') if current_user.is_admin else url_for('leave.dashboard'))
        
        leave_records = LeaveService.get_user_leave_records(user_id)
        
        # 計算年度請假統計
        current_year = datetime.now().year
        stats = LeaveService.calculate_annual_leave_stats(leave_records, current_year)
        
        return render_template(
            'user_records.html',
            user=user,
            leave_records=leave_records,
            current_year=current_year,
            **stats
        )
    except Exception as e:
        flash('載入用戶記錄時發生錯誤', 'danger')
        return redirect(url_for('admin.admin') if current_user.is_admin else url_for('leave.dashboard'))


@leave_bp.route('/delete_leave/<int:leave_id>', methods=['POST'])
@login_required
def delete_leave(leave_id):
    """刪除請假記錄"""
    try:
        user_id = LeaveService.delete_leave_record(leave_id, restore_days=True)
        flash('刪除請假紀錄成功', 'success')
        
        # 根據 referer 來決定跳轉頁面
        referer = request.headers.get("Referer")
        if referer and 'admin' in referer:
            return redirect(url_for('admin.admin'))
        else:
            return redirect(url_for('leave.user_records', user_id=user_id))
    except (BusinessLogicError, DatabaseError) as e:
        flash(str(e), 'danger')
        return redirect(url_for('leave.dashboard'))
    except Exception as e:
        flash('刪除請假記錄時發生未知錯誤', 'danger')
        return redirect(url_for('leave.dashboard'))