"""Quan ly danh muc: nha cung cap, loai hang, hang hoa, loai khach hang, kho (SD12) + in ma vach."""
from flask import Blueprint, render_template, request, Response, abort

from app.extensions import db
from app.models import NhaCungCap, LoaiHangHoa, HangHoa, LoaiKhachHang, Kho
from app.services import mavach, tonkho, LoiNghiepVu
from app.services.mavach import CHUAN_MA_VACH
from app.utils.crud import Crud, Truong as T
from app.utils.decorators import quyen_required

bp = Blueprint('danhmuc', __name__)

ncc = Crud(bp, 'ncc', 'nha-cung-cap', NhaCungCap, 'Nhà cung cấp', bieu_tuong='bi-truck', chuc_nang='danh_muc',
           cot_ma='ma_ncc', tim_kiem=('ma_ncc', 'ten_ncc', 'dien_thoai'),
           truong=[T('ma_ncc', 'Mã NCC', bat_buoc=True), T('ten_ncc', 'Tên nhà cung cấp', bat_buoc=True),
                   T('dien_thoai', 'Điện thoại'), T('email', 'Email', 'email'),
                   T('nguoi_lien_he', 'Người liên hệ'), T('ma_so_thue', 'Mã số thuế'),
                   T('dia_chi', 'Địa chỉ', rong=12), T('trang_thai', 'Đang giao dịch', 'bool')],
           cot=[('ma_ncc', 'Mã', None), ('ten_ncc', 'Tên NCC', None), ('dien_thoai', 'Điện thoại', None),
                ('nguoi_lien_he', 'Liên hệ', None), ('trang_thai', 'Trạng thái', 'bool')])

loai_hang = Crud(bp, 'loai_hang', 'loai-hang', LoaiHangHoa, 'Loại hàng hóa', bieu_tuong='bi-tags',
                 chuc_nang='danh_muc', cot_ma='ma_loai', tim_kiem=('ma_loai', 'ten_loai'),
                 truong=[T('ma_loai', 'Mã loại', bat_buoc=True), T('ten_loai', 'Tên loại', bat_buoc=True),
                         T('mo_ta', 'Mô tả', 'textarea', rong=12)],
                 cot=[('ma_loai', 'Mã', None), ('ten_loai', 'Tên loại', None), ('mo_ta', 'Mô tả', None)])


def _hh_mac_dinh(hh):
    if not hh.chuan_ma_vach:
        hh.chuan_ma_vach = 'ean13'


def _hh_sau_luu(hh, moi):
    db.session.flush()
    if not hh.ma_vach:
        hh.ma_vach = mavach.sinh_ean13(hh.id) if hh.chuan_ma_vach == 'ean13' else hh.ma_hang
    mavach.kiem_tra(hh.ma_vach, hh.chuan_ma_vach)
    if moi:  # tao dong ton kho = 0 o moi kho de theo doi min/max ngay tu dau
        for k in Kho.query.filter_by(trang_thai=True):
            tonkho.lay_ton_kho(hh.id, k.id, tao_moi=True)


def _hh_loc(q, args):
    if args.get('loai', type=int):
        q = q.filter(HangHoa.loai_hang_id == args.get('loai', type=int))
    if args.get('ncc', type=int):
        q = q.filter(HangHoa.nha_cung_cap_id == args.get('ncc', type=int))
    return q


hang_hoa = Crud(bp, 'hang_hoa', 'hang-hoa', HangHoa, 'Hàng hóa', bieu_tuong='bi-box-seam', chuc_nang='danh_muc',
                cot_ma='ma_hang', tim_kiem=('ma_hang', 'ma_vach', 'ten_hang'), mac_dinh=_hh_mac_dinh,
                sau_luu=_hh_sau_luu, loc=_hh_loc,
                truong=[T('ma_hang', 'Mã hàng', bat_buoc=True), T('ten_hang', 'Tên hàng', bat_buoc=True),
                        T('ma_vach', 'Mã vạch', goi_y='Để trống để tự sinh mã EAN-13'),
                        T('chuan_ma_vach', 'Chuẩn mã vạch', 'select', chon=CHUAN_MA_VACH, bat_buoc=True),
                        T('loai_hang_id', 'Loại hàng', 'select', model=LoaiHangHoa, cot_ma='ma_loai'),
                        T('nha_cung_cap_id', 'Nhà cung cấp', 'select', model=NhaCungCap, cot_ma='ma_ncc'),
                        T('don_vi_tinh', 'Đơn vị tính', bat_buoc=True),
                        T('gia_nhap', 'Giá nhập', 'number', min=0), T('gia_ban', 'Giá bán', 'number', min=0,
                                                                      bat_buoc=True),
                        T('han_su_dung', 'Hạn sử dụng', 'date'), T('xuat_xu', 'Xuất xứ'),
                        T('mo_ta', 'Mô tả', 'textarea', rong=12), T('trang_thai', 'Đang kinh doanh', 'bool')],
                cot=[('ma_hang', 'Mã', None), ('ten_hang', 'Tên hàng', None), ('ma_vach', 'Mã vạch', None),
                     ('loai_hang.ten_loai', 'Loại', None), ('don_vi_tinh', 'ĐVT', None),
                     ('gia_ban', 'Giá bán', 'vnd'), ('tong_ton', 'Tồn', 'so'), ('han_su_dung', 'HSD', 'ngay'),
                     ('trang_thai', 'Trạng thái', 'bool')],
                hanh_dong=[('In mã vạch', 'danhmuc.in_ma_vach', 'bi-upc-scan')])

loai_kh = Crud(bp, 'loai_kh', 'loai-khach-hang', LoaiKhachHang, 'Loại khách hàng', bieu_tuong='bi-people',
               chuc_nang='danh_muc', cot_ma='ma_loai', tim_kiem=('ma_loai', 'ten_loai'),
               truong=[T('ma_loai', 'Mã loại', bat_buoc=True), T('ten_loai', 'Tên loại', bat_buoc=True),
                       T('chiet_khau', 'Chiết khấu (%)', 'number', min=0),
                       T('han_muc_no', 'Hạn mức nợ (đ)', 'number', min=0, goi_y='0 = dùng mặc định hệ thống'),
                       T('so_ngay_no', 'Số ngày được nợ', 'number', min=0, goi_y='0 = dùng mặc định hệ thống'),
                       T('mo_ta', 'Mô tả', 'textarea', rong=12)],
               cot=[('ma_loai', 'Mã', None), ('ten_loai', 'Tên loại', None), ('chiet_khau', 'Chiết khấu %', 'so'),
                    ('han_muc_no', 'Hạn mức nợ', 'vnd'), ('so_ngay_no', 'Số ngày nợ', 'so')])

kho = Crud(bp, 'kho', 'kho', Kho, 'Kho', bieu_tuong='bi-building', chuc_nang='danh_muc', cot_ma='ma_kho',
           tim_kiem=('ma_kho', 'ten_kho'),
           truong=[T('ma_kho', 'Mã kho', bat_buoc=True), T('ten_kho', 'Tên kho', bat_buoc=True),
                   T('dia_chi', 'Địa chỉ', rong=12), T('trang_thai', 'Đang hoạt động', 'bool')],
           cot=[('ma_kho', 'Mã', None), ('ten_kho', 'Tên kho', None), ('dia_chi', 'Địa chỉ', None),
                ('trang_thai', 'Trạng thái', 'bool')])


@bp.route('/ma-vach/<chuan>/<ma>.svg')
def ma_vach_svg(chuan, ma):
    """Anh ma vach (cong khai: dung cho hoa don, the than thiet cua khach)."""
    try:
        return Response(mavach.svg(ma, chuan), mimetype='image/svg+xml',
                        headers={'Cache-Control': 'max-age=86400'})
    except LoiNghiepVu:
        abort(404)


@bp.route('/hang-hoa/in-ma-vach')
@bp.route('/hang-hoa/<int:id>/in-ma-vach')
@quyen_required('danh_muc', 'in_an')
def in_ma_vach(id=None):
    """In tem ma vach: chon hang, chuan ma va so luong tem."""
    ids = [id] if id else request.args.getlist('hh', type=int)
    so_tem = max(1, min(request.args.get('so_tem', 12, type=int), 200))
    hien_gia = request.args.get('gia', '1') == '1'
    chuan = request.args.get('chuan')
    ds = HangHoa.query.filter(HangHoa.id.in_(ids)).all() if ids else []
    tem, loi = [], []
    for hh in ds:
        c = chuan or hh.chuan_ma_vach
        ma = hh.ma_vach if c == hh.chuan_ma_vach else (hh.ma_hang if c in ('code128', 'code39') else hh.ma_vach)
        try:
            mavach.kiem_tra(ma, c)
            tem.append((hh, c, ma))
        except LoiNghiepVu as e:
            loi.append(f'{hh.ma_hang}: {e}')
    return render_template('danhmuc/ma_vach.html', tem=tem, loi=loi, so_tem=so_tem, hien_gia=hien_gia,
                           chuan=chuan, ids=ids, CHUAN=CHUAN_MA_VACH,
                           tat_ca=HangHoa.query.filter_by(trang_thai=True).order_by(HangHoa.ten_hang).all())
