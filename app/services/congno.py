"""Quan ly cong no theo chung tu va canh bao no (SD07, SD13)."""
from datetime import date, timedelta

from flask import url_for, current_app

from app.extensions import db
from app.models import CongNo, ThanhToanCongNo, KhachHang, PhieuNhap
from app.services import LoiNghiepVu, thongbao
from app.utils.filters import vnd


def tao_cong_no_kh(khach_hang, hoa_don, so_tien):
    cn = CongNo(doi_tuong='khach_hang', khach_hang=khach_hang, loai_chung_tu='hoa_don',
                ma_chung_tu=hoa_don.ma_hd, so_tien=so_tien,
                han_thanh_toan=date.today() + timedelta(days=khach_hang.so_ngay_no_ap_dung))
    db.session.add(cn)
    return cn


def tao_cong_no_ncc(ncc, phieu_nhap, so_tien, han_thanh_toan=None):
    cn = CongNo(doi_tuong='nha_cung_cap', nha_cung_cap=ncc, loai_chung_tu='phieu_nhap',
                ma_chung_tu=phieu_nhap.ma_phieu, so_tien=so_tien,
                han_thanh_toan=han_thanh_toan or date.today() + timedelta(days=current_app.config['SO_NGAY_NO_NCC']))
    db.session.add(cn)
    return cn


def tong_no_khach_hang(khach_hang_id):
    tong = (db.session.query(db.func.coalesce(db.func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
            .filter(CongNo.khach_hang_id == khach_hang_id).scalar())
    return float(tong or 0)


def thanh_toan(cong_no, so_tien, hinh_thuc, nguoi, ghi_chu=None):
    """Ghi nhan thu no khach hang / tra no nha cung cap tren 1 chung tu."""
    if so_tien <= 0:
        raise LoiNghiepVu('Số tiền thanh toán phải lớn hơn 0.')
    if so_tien > cong_no.con_lai + 0.001:
        raise LoiNghiepVu(f'Số tiền vượt quá số còn nợ của chứng từ ({vnd(cong_no.con_lai)}).')
    cong_no.thanh_toans.append(ThanhToanCongNo(so_tien=so_tien, hinh_thuc=hinh_thuc,
                                               nguoi_thuc_hien=nguoi, ghi_chu=ghi_chu))
    cong_no.da_thanh_toan = (cong_no.da_thanh_toan or 0) + so_tien
    if cong_no.loai_chung_tu == 'phieu_nhap':
        pn = PhieuNhap.query.filter_by(ma_phieu=cong_no.ma_chung_tu).first()
        if pn:
            pn.da_thanh_toan = (pn.da_thanh_toan or 0) + so_tien
    db.session.flush()
    kiem_tra_canh_bao_cong_no()


def kiem_tra_canh_bao_cong_no():
    """Canh bao khach hang no qua han (theo tung chung tu) va no vuot muc cho phep (theo tong no)."""
    mong_muon = {}
    ds = CongNo.query.filter(CongNo.doi_tuong == 'khach_hang', CongNo.so_tien > CongNo.da_thanh_toan).all()
    tong_theo_kh = {}
    for cn in ds:
        tong_theo_kh[cn.khach_hang_id] = tong_theo_kh.get(cn.khach_hang_id, 0) + cn.con_lai
        if cn.qua_han:
            mong_muon[f'no_qua_han:{cn.id}'] = (
                'no_qua_han',
                f'{cn.khach_hang.ho_ten} ({cn.khach_hang.ma_kh}) nợ {vnd(cn.con_lai)} theo chứng từ '
                f'{cn.ma_chung_tu}, quá hạn {cn.so_ngay_qua_han} ngày.',
                url_for('congno.chi_tiet', id=cn.id))
    for kh_id, tong in tong_theo_kh.items():
        kh = db.session.get(KhachHang, kh_id)
        if tong > kh.han_muc_no_ap_dung:
            mong_muon[f'no_vuot_muc:{kh_id}'] = (
                'no_vuot_muc',
                f'{kh.ho_ten} ({kh.ma_kh}) nợ tổng {vnd(tong)}, vượt mức cho phép '
                f'{vnd(kh.han_muc_no_ap_dung)}.',
                url_for('congno.danh_sach', doi_tuong='khach_hang', khach_hang_id=kh_id))
    return thongbao.dong_bo(['no_qua_han:', 'no_vuot_muc:'], mong_muon)
