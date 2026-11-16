"""Dong bo canh bao tu dong (lifeline 'Thong bao' trong SD06, SD07)."""
from datetime import datetime

from app.extensions import db
from app.models import ThongBao


def dong_bo(tien_to, mong_muon):
    """
    tien_to: danh sach tien to khoa thuoc nhom kiem tra (vd ['ton_thieu:', 'ton_vuot:']).
    mong_muon: {khoa: (loai, noi_dung, lien_ket)} - cac canh bao dang dung o thoi diem kiem tra.
    Tao canh bao moi, cap nhat noi dung canh bao cu, dong canh bao khong con dung.
    Tra ve so canh bao moi phat sinh.
    """
    dieu_kien = db.or_(*[ThongBao.khoa.like(t + '%') for t in tien_to])
    hien_co = {tb.khoa: tb for tb in ThongBao.query.filter(ThongBao.da_xu_ly.is_(False), dieu_kien)}
    so_moi = 0
    for khoa, (loai, noi_dung, lien_ket) in mong_muon.items():
        tb = hien_co.get(khoa)
        if tb:
            tb.noi_dung = noi_dung
        else:
            db.session.add(ThongBao(loai=loai, khoa=khoa, noi_dung=noi_dung, lien_ket=lien_ket))
            so_moi += 1
    for khoa, tb in hien_co.items():
        if khoa not in mong_muon:
            tb.da_xu_ly = True
            tb.ngay_xu_ly = datetime.now()
    db.session.flush()
    return so_moi


def kiem_tra_tat_ca():
    from app.services import tonkho, congno
    return tonkho.kiem_tra_canh_bao_ton_kho() + congno.kiem_tra_canh_bao_cong_no()
