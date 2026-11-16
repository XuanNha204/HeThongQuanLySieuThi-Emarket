"""Xu ly khach hang: the than thiet, tich diem (SD03)."""
from flask import current_app

from app.extensions import db
from app.models import KhachHang, TheThanhThiet, DonHang, HoaDon, LichSuDiem
from app.services import LoiNghiepVu
from app.utils.filters import vnd


def sinh_ma_kh():
    lon_nhat = db.session.query(db.func.max(KhachHang.ma_kh)).filter(KhachHang.ma_kh.like('KH%')).scalar()
    so = int(lon_nhat[2:]) + 1 if lon_nhat and lon_nhat[2:].isdigit() else 1
    return f'KH{so:04d}'


def lan_mua_cao_nhat(khach_hang):
    """Tra ve (gia tri, ma hoa don) cua lan mua co tong gia tri hang cao nhat."""
    row = (db.session.query(DonHang.tong_tien_hang, HoaDon.ma_hd).join(HoaDon)
           .filter(DonHang.khach_hang_id == khach_hang.id, DonHang.trang_thai == 'hoan_thanh')
           .order_by(DonHang.tong_tien_hang.desc()).first())
    return (row[0], row[1]) if row else (0, None)


def _tao_the(khach_hang, gia_tri, chung_tu):
    the = TheThanhThiet(ma_the=f'TTT{khach_hang.id:06d}', khach_hang=khach_hang,
                        gia_tri_dat_dieu_kien=gia_tri, chung_tu_dat_dieu_kien=chung_tu)
    db.session.add(the)
    return the


def xet_lap_the_tu_dong(khach_hang, gia_tri_lan_mua, chung_tu):
    """Goi khi thanh toan: lap the neu tong gia tri hang cua lan mua >= nguong."""
    if khach_hang.the_than_thiet is None and gia_tri_lan_mua >= current_app.config['NGUONG_THE_THAN_THIET']:
        return _tao_the(khach_hang, gia_tri_lan_mua, chung_tu)
    return None


def lap_the(khach_hang):
    """Nhan vien lap the: kiem tra dieu kien tren lich su mua hang."""
    if khach_hang.the_than_thiet is not None:
        raise LoiNghiepVu(f'Khách hàng đã có thẻ {khach_hang.the_than_thiet.ma_the}.')
    nguong = current_app.config['NGUONG_THE_THAN_THIET']
    gia_tri, ma_hd = lan_mua_cao_nhat(khach_hang)
    if gia_tri < nguong:
        raise LoiNghiepVu(f'Không đủ điều kiện: chưa có lần mua nào từ {vnd(nguong)} '
                          f'(lần mua cao nhất: {vnd(gia_tri)}).')
    return _tao_the(khach_hang, gia_tri, ma_hd)


def cong_diem(khach_hang, so_tien_thanh_toan, chung_tu):
    """Quy doi so tien mua hang thanh diem (chi ap dung khach co the than thiet)."""
    if not khach_hang.co_the:
        return 0
    diem = int(so_tien_thanh_toan // current_app.config['SO_TIEN_MOI_DIEM'])
    if diem > 0:
        khach_hang.diem_tich_luy = (khach_hang.diem_tich_luy or 0) + diem
        db.session.add(LichSuDiem(khach_hang=khach_hang, so_diem=diem, loai='tich_luy', chung_tu=chung_tu,
                                  mo_ta=f'Tích điểm hóa đơn {chung_tu}'))
    return diem


def tru_diem(khach_hang, so_diem, chung_tu):
    khach_hang.diem_tich_luy -= so_diem
    db.session.add(LichSuDiem(khach_hang=khach_hang, so_diem=-so_diem, loai='quy_doi', chung_tu=chung_tu,
                              mo_ta=f'Quy đổi điểm thanh toán {chung_tu}'))
