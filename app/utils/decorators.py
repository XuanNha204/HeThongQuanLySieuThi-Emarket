from functools import wraps

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user

from app.models import NguoiDung, KhachHang


def la_nhan_vien():
    return current_user.is_authenticated and isinstance(current_user, NguoiDung)


def la_khach_hang():
    return current_user.is_authenticated and isinstance(current_user, KhachHang)


def nhan_vien_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not la_nhan_vien():
            return redirect(url_for('auth.login', next=request.full_path))
        return f(*args, **kwargs)
    return wrapper


def quyen_required(chuc_nang, quyen='xem'):
    """Kiem tra quyen chi tiet cua nguoi dung tren chuc nang / chung tu."""
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not la_nhan_vien():
                return redirect(url_for('auth.login', next=request.full_path))
            if not current_user.co_quyen(chuc_nang, quyen):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return deco


def khach_hang_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not la_khach_hang():
            flash('Vui lòng đăng nhập tài khoản khách hàng.', 'warning')
            return redirect(url_for('portal.dang_nhap', next=request.full_path))
        return f(*args, **kwargs)
    return wrapper
