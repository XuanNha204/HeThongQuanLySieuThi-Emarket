"""Thong ke doanh thu theo ngay / thang / nam, theo hang hoa, theo nha cung cap (SD08)."""
from datetime import date, datetime, time

from app.extensions import db
from app.models import HoaDon, DonHang, ChiTietDonHang, HangHoa, NhaCungCap, PhieuNhap, CongNo, TonKho

KY = {
    'ngay': ('%Y-%m-%d', 'Ngày'),
    'thang': ('%Y-%m', 'Tháng'),
    'nam': ('%Y', 'Năm'),
}


def _khoang(tu_ngay, den_ngay):
    return datetime.combine(tu_ngay, time.min), datetime.combine(den_ngay, time.max)


def doanh_thu_theo_ky(ky, tu_ngay, den_ngay):
    """Moi dong: (ky, so hoa don, doanh thu, gia von, loi nhuan)."""
    fmt = KY[ky][0]
    bat_dau, ket_thuc = _khoang(tu_ngay, den_ngay)
    nhom = db.func.strftime(fmt, HoaDon.ngay_lap)
    hd_rows = (db.session.query(nhom, db.func.count(HoaDon.id), db.func.sum(HoaDon.tong_tien))
               .filter(HoaDon.ngay_lap.between(bat_dau, ket_thuc)).group_by(nhom).all())
    von_rows = (db.session.query(nhom, db.func.sum(ChiTietDonHang.so_luong * ChiTietDonHang.gia_von))
                .select_from(HoaDon).join(DonHang, HoaDon.don_hang_id == DonHang.id)
                .join(ChiTietDonHang, ChiTietDonHang.don_hang_id == DonHang.id)
                .filter(HoaDon.ngay_lap.between(bat_dau, ket_thuc)).group_by(nhom).all())
    von = {k: v or 0 for k, v in von_rows}
    ket_qua = []
    for k, so_hd, dt in sorted(hd_rows):
        dt = dt or 0
        ket_qua.append({'ky': _hien_thi_ky(ky, k), 'so_hoa_don': so_hd, 'doanh_thu': dt,
                        'gia_von': von.get(k, 0), 'loi_nhuan': dt - von.get(k, 0)})
    return ket_qua


def _hien_thi_ky(ky, k):
    if ky == 'ngay':
        y, m, d = k.split('-')
        return f'{d}/{m}/{y}'
    if ky == 'thang':
        y, m = k.split('-')
        return f'{m}/{y}'
    return k


def theo_hang_hoa(tu_ngay, den_ngay):
    bat_dau, ket_thuc = _khoang(tu_ngay, den_ngay)
    rows = (db.session.query(HangHoa, db.func.sum(ChiTietDonHang.so_luong),
                             db.func.sum(ChiTietDonHang.thanh_tien),
                             db.func.sum(ChiTietDonHang.so_luong * ChiTietDonHang.gia_von))
            .join(ChiTietDonHang, ChiTietDonHang.hang_hoa_id == HangHoa.id)
            .join(DonHang, ChiTietDonHang.don_hang_id == DonHang.id)
            .join(HoaDon, HoaDon.don_hang_id == DonHang.id)
            .filter(HoaDon.ngay_lap.between(bat_dau, ket_thuc))
            .group_by(HangHoa.id).order_by(db.func.sum(ChiTietDonHang.thanh_tien).desc()).all())
    return [{'ma': hh.ma_hang, 'ten': hh.ten_hang, 'dvt': hh.don_vi_tinh, 'so_luong': sl or 0,
             'doanh_thu': dt or 0, 'loi_nhuan': (dt or 0) - (von or 0), 'ton': hh.tong_ton}
            for hh, sl, dt, von in rows]


def theo_nha_cung_cap(tu_ngay, den_ngay):
    bat_dau, ket_thuc = _khoang(tu_ngay, den_ngay)
    nhap = dict(db.session.query(PhieuNhap.nha_cung_cap_id, db.func.sum(PhieuNhap.tong_tien))
                .filter(PhieuNhap.ngay_nhap.between(bat_dau, ket_thuc))
                .group_by(PhieuNhap.nha_cung_cap_id).all())
    ban = dict(db.session.query(HangHoa.nha_cung_cap_id, db.func.sum(ChiTietDonHang.thanh_tien))
               .join(ChiTietDonHang, ChiTietDonHang.hang_hoa_id == HangHoa.id)
               .join(DonHang, ChiTietDonHang.don_hang_id == DonHang.id)
               .join(HoaDon, HoaDon.don_hang_id == DonHang.id)
               .filter(HoaDon.ngay_lap.between(bat_dau, ket_thuc))
               .group_by(HangHoa.nha_cung_cap_id).all())
    no = dict(db.session.query(CongNo.nha_cung_cap_id, db.func.sum(CongNo.so_tien - CongNo.da_thanh_toan))
              .filter(CongNo.doi_tuong == 'nha_cung_cap').group_by(CongNo.nha_cung_cap_id).all())
    ket_qua = []
    for ncc in NhaCungCap.query.order_by(NhaCungCap.ten_ncc):
        dong = {'ma': ncc.ma_ncc, 'ten': ncc.ten_ncc, 'so_mat_hang': len(ncc.hang_hoas),
                'tien_nhap': nhap.get(ncc.id) or 0, 'doanh_thu': ban.get(ncc.id) or 0,
                'con_no': no.get(ncc.id) or 0}
        if dong['tien_nhap'] or dong['doanh_thu'] or dong['con_no'] or dong['so_mat_hang']:
            ket_qua.append(dong)
    return ket_qua


def tong_quan_hom_nay():
    bat_dau, ket_thuc = _khoang(date.today(), date.today())
    so_hd, dt = (db.session.query(db.func.count(HoaDon.id), db.func.coalesce(db.func.sum(HoaDon.tong_tien), 0))
                 .filter(HoaDon.ngay_lap.between(bat_dau, ket_thuc)).one())
    return {
        'so_hoa_don': so_hd, 'doanh_thu': dt,
        'don_cho': DonHang.query.filter(DonHang.trang_thai.in_(['cho_xu_ly', 'dang_xu_ly', 'dang_giao'])).count(),
        'ton_thieu': sum(1 for tk in TonKho.query.all() if tk.tinh_trang == 'thieu'),
        'no_kh': db.session.query(db.func.coalesce(db.func.sum(CongNo.so_tien - CongNo.da_thanh_toan), 0))
                   .filter(CongNo.doi_tuong == 'khach_hang').scalar(),
    }
