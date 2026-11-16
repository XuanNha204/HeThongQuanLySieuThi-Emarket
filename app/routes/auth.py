from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from app.models import NguoiDung
from app.utils.decorators import la_nhan_vien

bp = Blueprint('auth', __name__)


def _next_an_toan(default):
    nxt = request.args.get('next', '')
    return nxt if nxt.startswith('/') and not nxt.startswith('//') else default


@bp.route('/dang-nhap', methods=['GET', 'POST'])
def login():
    if la_nhan_vien():
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        nd = NguoiDung.query.filter_by(username=request.form.get('username', '').strip()).first()
        if nd and nd.check_password(request.form.get('password', '')):
            if not nd.trang_thai:
                flash('Tài khoản đã bị khóa. Liên hệ quản trị viên.', 'danger')
            else:
                login_user(nd, remember=bool(request.form.get('remember')))
                flash(f'Xin chào {nd.ho_ten}!', 'success')
                return redirect(_next_an_toan(url_for('dashboard.index')))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu.', 'danger')
    return render_template('auth/login.html')


@bp.route('/dang-xuat', methods=['POST'])
def logout():
    la_kh = current_user.is_authenticated and not la_nhan_vien()
    logout_user()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('portal.cua_hang' if la_kh else 'auth.login'))
