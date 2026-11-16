"""Xu ly ban hang: ap gia, dat hang, xu ly don, thanh toan (SD01, SD02, SD09, SD11)."""
import math

from flask import current_app

from app.extensions import db
from app.models import (GiaBanTheoKH, DonHang, ChiTietDonHang, LichSuDonHang, HoaDon, HangHoa, Kho,
                        HINH_THUC_TT)
from app.services import LoiNghiepVu, khachhang as kh_service, tonkho, congno
from app.utils.helpers import sinh_ma


def ap_gia(hang_hoa, khach_hang=None):
    """Don gia cho khach hang: gia rieng theo mat hang > chiet khau loai KH > gia niem yet."""
    if khach_hang is not None:
        rieng = GiaBanTheoKH.query.filter_by(khach_hang_id=khach_hang.id, hang_hoa_id=hang_hoa.id).first()
        if rieng:
            return rieng.gia_ban, 'Giá riêng'
        loai = khach_hang.loai_khach_hang
        if loai and loai.chiet_khau:
            return round(hang_hoa.gia_ban * (1 - loai.chiet_khau / 100), -2), f'Chiết khấu {loai.chiet_khau:g}%'
    return hang_hoa.gia_ban, None


def _gom_dong_hang(items):
    gop = {}
    for it in items:
        hh_id, sl = int(it.get('hang_hoa_id') or 0), int(it.get('so_luong') or 0)
        if hh_id and sl > 0:
            gop[hh_id] = gop.get(hh_id, 0) + sl
    if not gop:
        raise LoiNghiepVu('Đơn hàng phải có ít nhất 1 mặt hàng.')
    return gop


def _ghi_lich_su(don, trang_thai, nguoi, ghi_chu=None):
    don.lich_sus.append(LichSuDonHang(trang_thai=trang_thai, nguoi_thuc_hien=nguoi, ghi_chu=ghi_chu))


def tao_don_hang(khach_hang, items, kho_id, nguon='online', nguoi='', dia_chi_giao=None, ghi_chu=None):
    kho = db.session.get(Kho, kho_id) if kho_id else None
    if kho is None or not kho.trang_thai:
        raise LoiNghiepVu('Kho bán hàng không hợp lệ.')
    don = DonHang(ma_don=sinh_ma('DH', DonHang.ma_don), khach_hang=khach_hang, kho=kho, nguon=nguon,
                  dia_chi_giao=dia_chi_giao, ghi_chu=ghi_chu, trang_thai='cho_xu_ly')
    db.session.add(don)
    tong = 0
    for hh_id, sl in _gom_dong_hang(items).items():
        hh = db.session.get(HangHoa, hh_id)
        if hh is None or not hh.trang_thai:
            raise LoiNghiepVu('Có mặt hàng không tồn tại hoặc đã ngừng kinh doanh.')
        ton = hh.ton_tai_kho(kho.id)
        if ton < sl:
            raise LoiNghiepVu(f'"{hh.ten_hang}" chỉ còn {ton} {hh.don_vi_tinh} tại {kho.ten_kho}.')
        gia, _ = ap_gia(hh, khach_hang)
        don.chi_tiets.append(ChiTietDonHang(hang_hoa=hh, so_luong=sl, don_gia=gia, gia_niem_yet=hh.gia_ban,
                                            thanh_tien=gia * sl))
        tong += gia * sl
    don.tong_tien_hang = don.tong_thanh_toan = tong
    _ghi_lich_su(don, 'cho_xu_ly', nguoi, 'Tạo đơn hàng')
    db.session.flush()
    return don


def hoan_tat_don(don, nhan_vien, hinh_thuc_tt='tien_mat', diem_su_dung=0, tien_khach_dua=0):
    """Thanh toan don: tru ton kho, quy doi diem, lap hoa don, tich diem, lap the, ghi cong no."""
    if don.hoa_don is not None:
        raise LoiNghiepVu('Đơn hàng đã được thanh toán.')
    if hinh_thuc_tt not in HINH_THUC_TT:
        raise LoiNghiepVu('Hình thức thanh toán không hợp lệ.')
    kh = don.khach_hang
    if hinh_thuc_tt == 'ghi_no' and kh is None:
        raise LoiNghiepVu('Khách lẻ không thể ghi nợ. Vui lòng chọn khách hàng.')

    for ct in don.chi_tiets:
        tk = tonkho.lay_ton_kho(ct.hang_hoa_id, don.kho_id)
        if tk is None or tk.so_luong_ton < ct.so_luong:
            con = tk.so_luong_ton if tk else 0
            raise LoiNghiepVu(f'"{ct.hang_hoa.ten_hang}" không đủ tồn kho (còn {con}).')
        tk.so_luong_ton -= ct.so_luong
        tk.so_luong_da_ban += ct.so_luong
        ct.gia_von = ct.hang_hoa.gia_nhap

    ma_hd = sinh_ma('HD', HoaDon.ma_hd)
    giam = 0
    if diem_su_dung:
        if kh is None or not kh.co_the:
            raise LoiNghiepVu('Chỉ khách hàng có thẻ thân thiết mới được dùng điểm.')
        if diem_su_dung < 0 or diem_su_dung > (kh.diem_tich_luy or 0):
            raise LoiNghiepVu(f'Khách hàng chỉ có {kh.diem_tich_luy} điểm.')
        gia_tri_diem = current_app.config['GIA_TRI_MOT_DIEM']
        giam = min(diem_su_dung * gia_tri_diem, don.tong_tien_hang)
        diem_su_dung = math.ceil(giam / gia_tri_diem)
        kh_service.tru_diem(kh, diem_su_dung, ma_hd)
    don.diem_su_dung, don.giam_gia_diem = diem_su_dung, giam
    don.tong_thanh_toan = don.tong_tien_hang - giam

    if hinh_thuc_tt == 'tien_mat' and don.nguon == 'tai_quay' and tien_khach_dua < don.tong_thanh_toan:
        raise LoiNghiepVu('Tiền khách đưa chưa đủ.')

    hd = HoaDon(ma_hd=ma_hd, don_hang=don, nhan_vien=nhan_vien, tong_tien=don.tong_thanh_toan,
                hinh_thuc_tt=hinh_thuc_tt, tien_khach_dua=tien_khach_dua or don.tong_thanh_toan)
    db.session.add(hd)

    if kh is not None:
        kh.tong_mua = (kh.tong_mua or 0) + don.tong_thanh_toan
        kh_service.xet_lap_the_tu_dong(kh, don.tong_tien_hang, ma_hd)
        db.session.flush()
        don.diem_cong = kh_service.cong_diem(kh, don.tong_thanh_toan, ma_hd)
        if hinh_thuc_tt == 'ghi_no' and don.tong_thanh_toan > 0:
            congno.tao_cong_no_kh(kh, hd, don.tong_thanh_toan)

    don.trang_thai = 'hoan_thanh'
    don.nguoi_xu_ly = nhan_vien
    db.session.flush()
    tonkho.kiem_tra_canh_bao_ton_kho()
    congno.kiem_tra_canh_bao_cong_no()
    return hd


def thanh_toan_tai_quay(nhan_vien, khach_hang, items, kho_id, hinh_thuc_tt, diem_su_dung=0, tien_khach_dua=0):
    don = tao_don_hang(khach_hang, items, kho_id, nguon='tai_quay', nguoi=nhan_vien.ho_ten)
    hd = hoan_tat_don(don, nhan_vien, hinh_thuc_tt, diem_su_dung, tien_khach_dua)
    _ghi_lich_su(don, 'hoan_thanh', nhan_vien.ho_ten, f'Thanh toán tại quầy - {hd.ma_hd}')
    return hd


def chuyen_trang_thai(don, trang_thai_moi, nhan_vien, hinh_thuc_tt='tien_mat', ghi_chu=None):
    """Nhan vien xu ly don hang theo luong trang thai."""
    if trang_thai_moi not in don.trang_thai_tiep:
        raise LoiNghiepVu(f'Không thể chuyển đơn từ "{don.ten_trang_thai}" sang trạng thái này.')
    if trang_thai_moi == 'hoan_thanh':
        hd = hoan_tat_don(don, nhan_vien, hinh_thuc_tt)
        ghi_chu = f'{ghi_chu + " - " if ghi_chu else ""}Lập hóa đơn {hd.ma_hd}'
    else:
        don.trang_thai = trang_thai_moi
        don.nguoi_xu_ly = nhan_vien
    _ghi_lich_su(don, trang_thai_moi, nhan_vien.ho_ten, ghi_chu)


def huy_don_boi_khach(don, khach_hang):
    if don.khach_hang_id != khach_hang.id:
        raise LoiNghiepVu('Không tìm thấy đơn hàng.')
    if don.trang_thai != 'cho_xu_ly':
        raise LoiNghiepVu('Chỉ hủy được đơn hàng đang chờ xử lý.')
    don.trang_thai = 'da_huy'
    _ghi_lich_su(don, 'da_huy', khach_hang.ho_ten, 'Khách hàng hủy đơn')
