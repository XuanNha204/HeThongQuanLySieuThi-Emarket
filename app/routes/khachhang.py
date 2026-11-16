"""Quan ly khach hang, the than thiet, lich su mua hang va diem tich luy (SD03, SD04)."""
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request

from app.extensions import db
from app.models import KhachHang, LoaiKhachHang, TheThanhThiet, DonHang
from app.services import LoiNghiepVu, khachhang as kh_service, congno
from app.utils.crud import Crud, Truong as T
from app.utils.decorators import quyen_required

bp = Blueprint('khachhang', __name__)


def _kh_mac_dinh(kh):
    if not kh.ma_kh:
        kh.ma_kh = kh_service.sinh_ma_kh()


kh_crud = Crud(bp, 'kh', 'danh-sach', KhachHang, 'Khách hàng', bieu_tuong='bi-person-vcard',
               chuc_nang='khach_hang', cot_ma='ma_kh', tim_kiem=('ma_kh', 'ho_ten', 'dien_thoai', 'email'),
               sap_xep=KhachHang.id.desc(), mac_dinh=_kh_mac_dinh,
               truong=[T('ma_kh', 'Mã KH', goi_y='Để trống để tự sinh'), T('ho_ten', 'Họ tên', bat_buoc=True),
                       T('dien_thoai', 'Điện thoại', goi_y='Dùng để đăng nhập cổng khách hàng'),
                       T('email', 'Email', 'email'),
                       T('loai_kh_id', 'Loại khách hàng', 'select', model=LoaiKhachHang, cot_ma='ma_loai'),
                       T('han_muc_no', 'Hạn mức nợ riêng (đ)', 'number', goi_y='Bỏ trống = theo loại KH'),
                       T('dia_chi', 'Địa chỉ', rong=12),
                       T('mat_khau', 'Mật khẩu cổng khách hàng', 'password', excel=False,
                         goi_y='Bỏ trống nếu không đổi'),
                       T('trang_thai', 'Đang hoạt động', 'bool')],
               cot=[('ma_kh', 'Mã', None), ('ho_ten', 'Họ tên', None), ('dien_thoai', 'Điện thoại', None),
                    ('loai_khach_hang.ten_loai', 'Loại', None), ('the_than_thiet.ma_the', 'Thẻ TT', None),
                    ('diem_tich_luy', 'Điểm', 'so'), ('tong_mua', 'Tổng mua', 'vnd'),
                    ('trang_thai', 'Trạng thái', 'bool')],
               hanh_dong=[('Chi tiết', 'khachhang.chi_tiet', 'bi-eye')])


@bp.route('/<int:id>')
@quyen_required('khach_hang', 'xem')
def chi_tiet(id):
    kh = db.session.get(KhachHang, id) or abort(404)
    lan_mua, ma_hd = kh_service.lan_mua_cao_nhat(kh)
    don_hangs = DonHang.query.filter_by(khach_hang_id=kh.id).order_by(DonHang.ngay_dat.desc()).limit(50).all()
    return render_template('khachhang/chi_tiet.html', kh=kh, don_hangs=don_hangs, lan_mua=lan_mua, ma_hd=ma_hd,
                           tong_no=congno.tong_no_khach_hang(kh.id))


@bp.route('/<int:id>/lap-the', methods=['POST'])
@quyen_required('khach_hang', 'them')
def lap_the(id):
    kh = db.session.get(KhachHang, id) or abort(404)
    try:
        the = kh_service.lap_the(kh)
        db.session.commit()
        flash(f'Đã lập thẻ thân thiết {the.ma_the} cho {kh.ho_ten}.', 'success')
    except LoiNghiepVu as e:
        db.session.rollback()
        flash(str(e), 'warning')
    return redirect(url_for('khachhang.chi_tiet', id=id))


@bp.route('/<int:id>/khoa-the', methods=['POST'])
@quyen_required('khach_hang', 'sua')
def khoa_the(id):
    kh = db.session.get(KhachHang, id) or abort(404)
    if kh.the_than_thiet:
        kh.the_than_thiet.trang_thai = not kh.the_than_thiet.trang_thai
        db.session.commit()
        flash('Đã ' + ('mở khóa' if kh.the_than_thiet.trang_thai else 'khóa') + ' thẻ thân thiết.', 'info')
    return redirect(url_for('khachhang.chi_tiet', id=id))


@bp.route('/the-than-thiet')
@quyen_required('khach_hang', 'xem')
def the_than_thiet():
    q = TheThanhThiet.query.join(KhachHang)
    tu_khoa = request.args.get('q', '').strip()
    if tu_khoa:
        q = q.filter(db.or_(TheThanhThiet.ma_the.ilike(f'%{tu_khoa}%'), KhachHang.ho_ten.ilike(f'%{tu_khoa}%'),
                            KhachHang.dien_thoai.ilike(f'%{tu_khoa}%')))
    return render_template('khachhang/the_than_thiet.html', ds=q.order_by(TheThanhThiet.ngay_lap.desc()).all())
