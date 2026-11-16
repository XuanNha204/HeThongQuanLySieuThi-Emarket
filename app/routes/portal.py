"""Cong khach hang: dat hang online, quan ly & theo doi don hang, the than thiet, diem (SD01, SD02, SD04)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from flask_login import login_user, current_user

from app.extensions import db
from app.models import HangHoa, LoaiHangHoa, KhachHang, Kho, DonHang
from app.services import LoiNghiepVu, banhang, khachhang as kh_service, congno
from app.utils.decorators import khach_hang_required, la_khach_hang

bp = Blueprint('portal', __name__)


def _kh():
    return current_user if la_khach_hang() else None


def _gio():
    return {int(k): v for k, v in session.get('gio_hang', {}).items()}


def _luu_gio(gio):
    session['gio_hang'] = {str(k): v for k, v in gio.items() if v > 0}


@bp.app_context_processor
def _so_luong_gio():
    return {'so_mon_gio': sum(session.get('gio_hang', {}).values())}


# ---------------------------------------------------------------- tai khoan
@bp.route('/dang-nhap', methods=['GET', 'POST'])
def dang_nhap():
    if la_khach_hang():
        return redirect(url_for('portal.cua_hang'))
    if request.method == 'POST':
        kh = KhachHang.query.filter_by(dien_thoai=request.form.get('dien_thoai', '').strip()).first()
        if kh and kh.check_password(request.form.get('mat_khau', '')) and kh.trang_thai:
            login_user(kh, remember=True)
            flash(f'Xin chào {kh.ho_ten}!', 'success')
            nxt = request.args.get('next', '')
            return redirect(nxt if nxt.startswith('/khach') else url_for('portal.cua_hang'))
        flash('Số điện thoại hoặc mật khẩu không đúng.', 'danger')
    return render_template('portal/dang_nhap.html')


@bp.route('/dang-ky', methods=['GET', 'POST'])
def dang_ky():
    if request.method == 'POST':
        f = request.form
        dt, ten, mk = f.get('dien_thoai', '').strip(), f.get('ho_ten', '').strip(), f.get('mat_khau', '')
        kh = KhachHang.query.filter_by(dien_thoai=dt).first() if dt else None
        if not dt.isdigit() or len(dt) < 9 or not ten:
            flash('Vui lòng nhập họ tên và số điện thoại hợp lệ.', 'danger')
        elif len(mk) < 6 or mk != f.get('nhap_lai'):
            flash('Mật khẩu tối thiểu 6 ký tự và phải nhập lại trùng khớp.', 'danger')
        elif kh and kh.mat_khau_hash:
            flash('Số điện thoại đã được đăng ký. Vui lòng đăng nhập.', 'warning')
        else:
            if kh is None:  # KH moi; neu KH da mua tai quay (chua co mat khau) thi kich hoat tai khoan
                kh = KhachHang(ma_kh=kh_service.sinh_ma_kh(), dien_thoai=dt, ho_ten=ten)
                db.session.add(kh)
            kh.email, kh.dia_chi = f.get('email') or kh.email, f.get('dia_chi') or kh.dia_chi
            kh.set_password(mk)
            db.session.commit()
            login_user(kh, remember=True)
            flash('Đăng ký thành công!', 'success')
            return redirect(url_for('portal.cua_hang'))
    return render_template('portal/dang_ky.html')


@bp.route('/tai-khoan', methods=['GET', 'POST'])
@khach_hang_required
def tai_khoan():
    kh = current_user
    if request.method == 'POST':
        f = request.form
        if f.get('ho_ten', '').strip():
            kh.ho_ten = f['ho_ten'].strip()
        kh.email, kh.dia_chi = f.get('email') or None, f.get('dia_chi') or None
        if f.get('mat_khau_moi'):
            if not kh.check_password(f.get('mat_khau_cu', '')):
                flash('Mật khẩu hiện tại không đúng.', 'danger')
                return redirect(url_for('portal.tai_khoan'))
            if len(f['mat_khau_moi']) < 6:
                flash('Mật khẩu mới tối thiểu 6 ký tự.', 'danger')
                return redirect(url_for('portal.tai_khoan'))
            kh.set_password(f['mat_khau_moi'])
        db.session.commit()
        flash('Đã cập nhật thông tin tài khoản.', 'success')
        return redirect(url_for('portal.tai_khoan'))
    lan_mua, _ = kh_service.lan_mua_cao_nhat(kh)
    return render_template('portal/tai_khoan.html', kh=kh, lan_mua=lan_mua,
                           tong_no=congno.tong_no_khach_hang(kh.id))


# ---------------------------------------------------------------- mua sam
@bp.route('/')
def cua_hang():
    kh = _kh()
    q = HangHoa.query.filter_by(trang_thai=True)
    loai = request.args.get('loai', type=int)
    if loai:
        q = q.filter_by(loai_hang_id=loai)
    tu_khoa = request.args.get('q', '').strip()
    if tu_khoa:
        q = q.filter(db.or_(HangHoa.ten_hang.ilike(f'%{tu_khoa}%'), HangHoa.ma_vach == tu_khoa))
    trang = q.order_by(HangHoa.ten_hang).paginate(page=request.args.get('page', 1, type=int), per_page=24,
                        error_out=False)
    gia = {hh.id: banhang.ap_gia(hh, kh) for hh in trang.items}
    return render_template('portal/cua_hang.html', trang=trang, gia=gia, loai=loai,
                           loais=LoaiHangHoa.query.order_by(LoaiHangHoa.ten_loai).all())


@bp.route('/gio-hang/them', methods=['POST'])
def them_vao_gio():
    hh = db.session.get(HangHoa, request.form.get('hang_hoa_id', type=int) or 0)
    if hh is None or not hh.trang_thai:
        abort(404)
    gio = _gio()
    gio[hh.id] = gio.get(hh.id, 0) + max(1, request.form.get('so_luong', 1, type=int))
    _luu_gio(gio)
    flash(f'Đã thêm "{hh.ten_hang}" vào giỏ hàng.', 'success')
    return redirect(request.referrer or url_for('portal.cua_hang'))


@bp.route('/gio-hang', methods=['GET', 'POST'])
def gio_hang():
    gio = _gio()
    if request.method == 'POST':  # cap nhat so luong
        for hh_id in list(gio):
            gio[hh_id] = max(0, request.form.get(f'sl_{hh_id}', gio[hh_id], type=int))
        gio.pop(request.form.get('xoa', type=int), None)
        _luu_gio(gio)
        return redirect(url_for('portal.gio_hang'))
    kh = _kh()
    dong, tong = [], 0
    for hh in HangHoa.query.filter(HangHoa.id.in_(gio)).all() if gio else []:
        don_gia, ghi_chu = banhang.ap_gia(hh, kh)
        dong.append({'hh': hh, 'sl': gio[hh.id], 'don_gia': don_gia, 'ghi_chu': ghi_chu,
                     'thanh_tien': don_gia * gio[hh.id]})
        tong += don_gia * gio[hh.id]
    return render_template('portal/gio_hang.html', dong=dong, tong=tong, kh=kh,
                           khos=Kho.query.filter_by(trang_thai=True).order_by(Kho.ma_kho).all())


@bp.route('/dat-hang', methods=['POST'])
@khach_hang_required
def dat_hang():
    gio = _gio()
    if not gio:
        flash('Giỏ hàng đang trống.', 'warning')
        return redirect(url_for('portal.cua_hang'))
    dia_chi = request.form.get('dia_chi_giao', '').strip()
    if not dia_chi:
        flash('Vui lòng nhập địa chỉ giao hàng.', 'danger')
        return redirect(url_for('portal.gio_hang'))
    try:
        don = banhang.tao_don_hang(current_user, [{'hang_hoa_id': k, 'so_luong': v} for k, v in gio.items()],
                                   request.form.get('kho_id', type=int), 'online', current_user.ho_ten, dia_chi,
                                   request.form.get('ghi_chu') or None)
        db.session.commit()
    except LoiNghiepVu as e:
        db.session.rollback()
        flash(str(e), 'danger')
        return redirect(url_for('portal.gio_hang'))
    session.pop('gio_hang', None)
    flash(f'Đặt hàng thành công! Mã đơn: {don.ma_don}.', 'success')
    return redirect(url_for('portal.chi_tiet_don', id=don.id))


@bp.route('/don-hang')
@khach_hang_required
def don_hang():
    ds = DonHang.query.filter_by(khach_hang_id=current_user.id).order_by(DonHang.ngay_dat.desc()).all()
    return render_template('portal/don_hang.html', ds=ds)


@bp.route('/don-hang/<int:id>')
@khach_hang_required
def chi_tiet_don(id):
    don = db.session.get(DonHang, id)
    if don is None or don.khach_hang_id != current_user.id:
        abort(404)
    return render_template('portal/don_hang_chi_tiet.html', don=don)


@bp.route('/don-hang/<int:id>/huy', methods=['POST'])
@khach_hang_required
def huy_don(id):
    don = db.session.get(DonHang, id) or abort(404)
    try:
        banhang.huy_don_boi_khach(don, current_user)
        db.session.commit()
        flash(f'Đã hủy đơn {don.ma_don}.', 'info')
    except LoiNghiepVu as e:
        db.session.rollback()
        flash(str(e), 'danger')
    return redirect(url_for('portal.chi_tiet_don', id=id))
