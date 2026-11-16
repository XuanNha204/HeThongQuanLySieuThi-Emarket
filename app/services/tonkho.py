"""Xu ly nhap hang va quan ly ton kho (SD05, SD06, SD14)."""
from flask import url_for

from app.extensions import db
from app.models import TonKho, HangHoa, PhieuNhap, ChiTietPhieuNhap, NhaCungCap, Kho
from app.services import LoiNghiepVu, thongbao
from app.utils.helpers import sinh_ma


def lay_ton_kho(hang_hoa_id, kho_id, tao_moi=False):
    tk = TonKho.query.filter_by(hang_hoa_id=hang_hoa_id, kho_id=kho_id).first()
    if tk is None and tao_moi:
        tk = TonKho(hang_hoa_id=hang_hoa_id, kho_id=kho_id, so_luong_ton=0, so_luong_da_ban=0)
        db.session.add(tk)
    return tk


def nhap_hang(nguoi_nhap, nha_cung_cap_id, kho_id, dong_hang, da_thanh_toan=0, han_thanh_toan=None, ghi_chu=None):
    """dong_hang: [{'hang_hoa_id', 'so_luong', 'don_gia', 'han_su_dung'}]"""
    from app.services import congno

    ncc = db.session.get(NhaCungCap, nha_cung_cap_id) if nha_cung_cap_id else None
    if not ncc or not ncc.trang_thai:
        raise LoiNghiepVu('Nhà cung cấp không hợp lệ hoặc đã ngừng giao dịch.')
    kho = db.session.get(Kho, kho_id) if kho_id else None
    if not kho or not kho.trang_thai:
        raise LoiNghiepVu('Vui lòng chọn kho nhập hợp lệ.')
    dong_hang = [d for d in dong_hang if d.get('hang_hoa_id') and d.get('so_luong', 0) > 0]
    if not dong_hang:
        raise LoiNghiepVu('Phiếu nhập phải có ít nhất 1 mặt hàng với số lượng > 0.')

    pn = PhieuNhap(ma_phieu=sinh_ma('PN', PhieuNhap.ma_phieu), nha_cung_cap=ncc, kho=kho,
                   nguoi_nhap=nguoi_nhap, ghi_chu=ghi_chu)
    db.session.add(pn)
    tong = 0
    for d in dong_hang:
        hh = db.session.get(HangHoa, d['hang_hoa_id'])
        if hh is None:
            raise LoiNghiepVu('Mặt hàng không tồn tại.')
        if d['don_gia'] < 0:
            raise LoiNghiepVu(f'Đơn giá nhập của "{hh.ten_hang}" không hợp lệ.')
        thanh_tien = d['so_luong'] * d['don_gia']
        pn.chi_tiets.append(ChiTietPhieuNhap(hang_hoa=hh, so_luong=d['so_luong'], don_gia=d['don_gia'],
                                             thanh_tien=thanh_tien, han_su_dung=d.get('han_su_dung')))
        tk = lay_ton_kho(hh.id, kho.id, tao_moi=True)
        tk.so_luong_ton += d['so_luong']
        hh.gia_nhap = d['don_gia']
        if d.get('han_su_dung'):
            hh.han_su_dung = d['han_su_dung']
        tong += thanh_tien

    if da_thanh_toan < 0 or da_thanh_toan > tong:
        raise LoiNghiepVu('Số tiền đã thanh toán phải từ 0 đến tổng tiền phiếu nhập.')
    pn.tong_tien = tong
    pn.da_thanh_toan = da_thanh_toan
    db.session.flush()

    if tong - da_thanh_toan > 0:
        congno.tao_cong_no_ncc(ncc, pn, tong - da_thanh_toan, han_thanh_toan)
    kiem_tra_canh_bao_ton_kho()
    return pn


def kiem_tra_canh_bao_ton_kho():
    """So sanh ton kho tung kho voi nguong min/max va sinh canh bao."""
    mong_muon = {}
    ds = (TonKho.query.join(HangHoa).join(Kho)
          .filter(HangHoa.trang_thai.is_(True), Kho.trang_thai.is_(True)).all())
    for tk in ds:
        hh, kho = tk.hang_hoa, tk.kho
        lien_ket = url_for('tonkho.index', kho_id=kho.id)
        if tk.tinh_trang == 'thieu':
            mong_muon[f'ton_thieu:{tk.id}'] = (
                'ton_kho_thieu',
                f'{hh.ten_hang} tại {kho.ten_kho} còn {tk.so_luong_ton} {hh.don_vi_tinh}, '
                f'dưới mức tối thiểu {tk.muc_toi_thieu}.', lien_ket)
        elif tk.tinh_trang == 'vuot':
            mong_muon[f'ton_vuot:{tk.id}'] = (
                'ton_kho_vuot',
                f'{hh.ten_hang} tại {kho.ten_kho} tồn {tk.so_luong_ton} {hh.don_vi_tinh}, '
                f'vượt mức tối đa {tk.muc_toi_da}.', lien_ket)
    return thongbao.dong_bo(['ton_thieu:', 'ton_vuot:'], mong_muon)
