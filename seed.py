"""Tao du lieu mau cho moi truong dev.

    python seed.py            # chi tao khi CSDL con trong
    python seed.py --reset    # xoa toan bo du lieu va tao lai

Du lieu ban hang duoc mo phong qua chinh cac service nghiep vu (ban tai quay, dat online, nhap hang,
thu no...) roi lui ngay chung tu ve qua khu, nen so lieu ton kho / cong no / diem luon khop nhau.
"""
import math
import random
import sys
from datetime import datetime, date, timedelta

from app import create_app
from app.extensions import db
from app.models import (NguoiDung, NhaCungCap, LoaiHangHoa, HangHoa, LoaiKhachHang, Kho, KhachHang, TonKho,
                        GiaBanTheoKH, DonHang, CongNo, LichSuDiem, TheThanhThiet)
from app.services import banhang, tonkho, congno, thongbao, mavach
from app.utils import helpers

SO_NGAY_MO_PHONG = 365

KHO = [('CN01', 'Chi nhánh Quận 1', '12 Lê Lợi, P. Bến Nghé, Q.1, TP.HCM'),
       ('CN02', 'Chi nhánh Thủ Đức', '45 Võ Văn Ngân, TP. Thủ Đức, TP.HCM')]

NCC = [('NCC01', 'Công ty CP Sữa Việt Nam (Vinamilk)', 'Q.7, TP.HCM', '02854155555', 'Trần Thu Hà'),
       ('NCC02', 'Công ty TNHH Nước giải khát Suntory PepsiCo VN', 'Q.1, TP.HCM', '02838219437', 'Lê Minh Quân'),
       ('NCC03', 'Công ty CP Acecook Việt Nam', 'Tân Phú, TP.HCM', '02838154064', 'Phạm Văn Tài'),
       ('NCC04', 'Công ty CP Hàng tiêu dùng Masan', 'Q.1, TP.HCM', '02862563862', 'Ngô Thanh Tâm'),
       ('NCC05', 'Công ty TNHH Quốc tế Unilever Việt Nam', 'Q.7, TP.HCM', '02854135686', 'Đỗ Hải Yến'),
       ('NCC06', 'Công ty CP Bibica', 'Q.3, TP.HCM', '02839717920', 'Vũ Quốc Bảo')]

LOAI_HANG = [('LH01', 'Sữa & chế phẩm'), ('LH02', 'Đồ uống'), ('LH03', 'Mì & thực phẩm khô'),
             ('LH04', 'Gia vị'), ('LH05', 'Bánh kẹo'), ('LH06', 'Hóa mỹ phẩm')]

# ma, ten, loai, ncc, dvt, gia nhap, gia ban, xuat xu, so ngay HSD, mo ta
HANG_HOA = [
    ('HH001', 'Sữa tươi Vinamilk 100% có đường 180ml', 'LH01', 'NCC01', 'Hộp', 6500, 8000, 'Việt Nam', 60, 'Sữa tươi tiệt trùng'),
    ('HH002', 'Sữa tươi Vinamilk không đường 1L', 'LH01', 'NCC01', 'Hộp', 29000, 35000, 'Việt Nam', 45, None),
    ('HH003', 'Sữa chua Vinamilk có đường 100g', 'LH01', 'NCC01', 'Hộp', 5200, 7000, 'Việt Nam', 3, 'Bảo quản 2–8°C'),
    ('HH004', 'Sữa đặc Ông Thọ đỏ 380g', 'LH01', 'NCC01', 'Lon', 21000, 26000, 'Việt Nam', 300, None),
    ('HH005', 'Pepsi Cola lon 330ml', 'LH02', 'NCC02', 'Lon', 8000, 10500, 'Việt Nam', 270, None),
    ('HH006', '7Up lon 330ml', 'LH02', 'NCC02', 'Lon', 8000, 10500, 'Việt Nam', 270, None),
    ('HH007', 'Nước tăng lực Sting dâu 330ml', 'LH02', 'NCC02', 'Chai', 8500, 11000, 'Việt Nam', 240, None),
    ('HH008', 'Trà Olong Tea+ Plus 450ml', 'LH02', 'NCC02', 'Chai', 8000, 11000, 'Việt Nam', 240, None),
    ('HH009', 'Nước tinh khiết Aquafina 500ml', 'LH02', 'NCC02', 'Chai', 4000, 6000, 'Việt Nam', 365, None),
    ('HH010', 'Mì Hảo Hảo tôm chua cay 75g', 'LH03', 'NCC03', 'Gói', 3600, 4500, 'Việt Nam', 180, 'Mì ăn liền bán chạy'),
    ('HH011', 'Mì Đệ Nhất thịt bằm 82g', 'LH03', 'NCC03', 'Gói', 4800, 6500, 'Việt Nam', 180, None),
    ('HH012', 'Phở bò Đệ Nhất 65g', 'LH03', 'NCC03', 'Gói', 6000, 8000, 'Việt Nam', 180, None),
    ('HH013', 'Miến Phú Hương sườn heo 58g', 'LH03', 'NCC03', 'Gói', 7000, 9500, 'Việt Nam', 240, None),
    ('HH014', 'Mì Omachi xốt bò hầm 80g', 'LH03', 'NCC04', 'Gói', 7000, 9000, 'Việt Nam', 180, None),
    ('HH015', 'Nước mắm Nam Ngư 500ml', 'LH04', 'NCC04', 'Chai', 32000, 39000, 'Việt Nam', 540, None),
    ('HH016', 'Nước tương Chin-su 250ml', 'LH04', 'NCC04', 'Chai', 14000, 18000, 'Việt Nam', 540, None),
    ('HH017', 'Tương ớt Chin-su 250g', 'LH04', 'NCC04', 'Chai', 12000, 15500, 'Việt Nam', 365, None),
    ('HH018', 'Hạt nêm Knorr thịt thăn 400g', 'LH04', 'NCC05', 'Gói', 32000, 39500, 'Việt Nam', 450, None),
    ('HH019', 'Bánh Hura Deli bông lan kem 336g', 'LH05', 'NCC06', 'Hộp', 42000, 52000, 'Việt Nam', 150, None),
    ('HH020', 'Kẹo sữa Bibica 150g', 'LH05', 'NCC06', 'Gói', 17000, 22000, 'Việt Nam', 300, None),
    ('HH021', 'Bánh quy bơ Bibica 400g', 'LH05', 'NCC06', 'Hộp', 58000, 72000, 'Việt Nam', 240, 'Quà biếu'),
    ('HH022', 'Nước giặt OMO Matic cửa trên 2.9kg', 'LH06', 'NCC05', 'Túi', 165000, 199000, 'Việt Nam', None, None),
    ('HH023', 'Dầu gội Clear bạc hà 630g', 'LH06', 'NCC05', 'Chai', 145000, 175000, 'Thái Lan', None, None),
    ('HH024', 'Kem đánh răng P/S than hoạt tính 230g', 'LH06', 'NCC05', 'Tuýp', 29000, 36000, 'Việt Nam', None, None),
    ('HH025', 'Nước rửa chén Sunlight chanh 750g', 'LH06', 'NCC05', 'Chai', 28000, 35000, 'Việt Nam', None, None),
    ('HH026', 'Xà bông Lifebuoy bảo vệ vượt trội 90g', 'LH06', 'NCC05', 'Cục', 11000, 14000, 'Việt Nam', None, None),
]

LOAI_KH = [('LKH01', 'Khách thường', 0, 0, 0, 'Khách mua lẻ'),
           ('LKH02', 'Khách VIP', 3, 0, 0, 'Giảm 3% trên giá niêm yết'),
           ('LKH03', 'Đại lý / doanh nghiệp', 8, 20_000_000, 30, 'Giảm 8%, được mua ghi nợ tới 20 triệu')]

# dien thoai, ho ten, loai, dia chi
KHACH_HANG = [
    ('0901234567', 'Nguyễn Văn An', 'LKH02', '25 Nguyễn Trãi, Q.5, TP.HCM'),
    ('0912345678', 'Trần Thị Bích', 'LKH01', '102 Cách Mạng Tháng 8, Q.3, TP.HCM'),
    ('0987654321', 'Lê Hoàng Cường', 'LKH01', '8 Kha Vạn Cân, TP. Thủ Đức'),
    ('0934567890', 'Phạm Thu Dung', 'LKH02', '77 Hai Bà Trưng, Q.1, TP.HCM'),
    ('0978123456', 'Võ Minh Em', 'LKH01', '19 Lê Văn Việt, TP. Thủ Đức'),
    ('0909888777', 'Đặng Quốc Phong', 'LKH01', '5 Điện Biên Phủ, Bình Thạnh'),
    ('0918777666', 'Bùi Thị Giang', 'LKH01', '66 Phan Văn Trị, Gò Vấp'),
    ('0936555444', 'Hồ Gia Huy', 'LKH02', '12 Nguyễn Văn Linh, Q.7'),
    ('0903111222', 'Tạp hóa Minh Anh', 'LKH03', '210 Hoàng Diệu 2, TP. Thủ Đức'),
    ('0283999888', 'Công ty TNHH Hoàng Phát', 'LKH03', 'KCN Tân Bình, Q. Tân Phú'),
    ('0977000111', 'Ngô Thị Kim', 'LKH01', '3 Trần Hưng Đạo, Q.1'),
    ('0966222333', 'Mai Văn Lực', 'LKH01', '48 Tô Ngọc Vân, TP. Thủ Đức'),
]

NHAN_VIEN = [('admin', 'admin123', 'Quản trị hệ thống', 'admin'),
             ('quanly1', '123456', 'Nguyễn Thị Quản Lý', 'quan_ly'),
             ('nhanvien1', '123456', 'Trần Văn Bán Hàng', 'ban_hang'),
             ('nhanvien2', '123456', 'Lý Thu Ngân', 'ban_hang'),
             ('kho1', '123456', 'Phạm Văn Thủ Kho', 'kho')]


class _DongHo(datetime):
    """Thay datetime trong helpers de ma chung tu sinh theo ngay mo phong."""
    hien_tai = None

    @classmethod
    def now(cls, tz=None):
        return cls.hien_tai or datetime.now()


def _danh_muc():
    khos = {m: Kho(ma_kho=m, ten_kho=t, dia_chi=d, trang_thai=True) for m, t, d in KHO}
    nccs = {m: NhaCungCap(ma_ncc=m, ten_ncc=t, dia_chi=d, dien_thoai=dt, nguoi_lien_he=lh, trang_thai=True)
            for m, t, d, dt, lh in NCC}
    loais = {m: LoaiHangHoa(ma_loai=m, ten_loai=t) for m, t in LOAI_HANG}
    db.session.add_all([*khos.values(), *nccs.values(), *loais.values()])
    hhs = {}
    for i, (ma, ten, loai, ncc, dvt, gn, gb, xx, hsd, mo_ta) in enumerate(HANG_HOA, start=1):
        hhs[ma] = HangHoa(ma_hang=ma, ma_vach=mavach.sinh_ean13(i), chuan_ma_vach='ean13', ten_hang=ten,
                          loai_hang=loais[loai], nha_cung_cap=nccs[ncc], don_vi_tinh=dvt, gia_nhap=gn, gia_ban=gb,
                          xuat_xu=xx, mo_ta=mo_ta, trang_thai=True,
                          han_su_dung=date.today() + timedelta(days=hsd) if hsd else None)
    db.session.add_all(hhs.values())
    db.session.flush()
    for hh in hhs.values():
        hmp = hh.loai_hang.ma_loai == 'LH06'
        for kho in khos.values():
            db.session.add(TonKho(hang_hoa=hh, kho=kho, so_luong_ton=0, so_luong_da_ban=0,
                                  muc_toi_thieu=10 if hmp else 30, muc_toi_da=200 if hmp else 600))
    loai_kh = {m: LoaiKhachHang(ma_loai=m, ten_loai=t, chiet_khau=ck, han_muc_no=hm, so_ngay_no=sn, mo_ta=mt)
               for m, t, ck, hm, sn, mt in LOAI_KH}
    db.session.add_all(loai_kh.values())
    khs = []
    for i, (dt, ten, loai, dc) in enumerate(KHACH_HANG, start=1):
        kh = KhachHang(ma_kh=f'KH{i:04d}', ho_ten=ten, dien_thoai=dt, dia_chi=dc, loai_khach_hang=loai_kh[loai],
                       email=f'kh{i:02d}@example.com', tong_mua=0, diem_tich_luy=0, trang_thai=True)
        kh.set_password('123456')
        khs.append(kh)
    db.session.add_all(khs)
    nvs = []
    for u, pw, ten, vt in NHAN_VIEN:
        nd = NguoiDung(username=u, ho_ten=ten, vai_tro=vt, trang_thai=True, email=f'{u}@emarket.vn')
        nd.set_password(pw)
        nd.ap_quyen_mac_dinh()
        nvs.append(nd)
    db.session.add_all(nvs)
    db.session.flush()
    # gia ban rieng cho khach dai ly
    kh_ma = {k.dien_thoai: k for k in khs}
    for dt, ma, gia in [('0283999888', 'HH005', 9000), ('0283999888', 'HH009', 5000), ('0283999888', 'HH010', 4000),
                        ('0903111222', 'HH010', 4100), ('0903111222', 'HH015', 36000)]:
        db.session.add(GiaBanTheoKH(khach_hang=kh_ma[dt], hang_hoa=hhs[ma], gia_ban=gia, ghi_chu='Hợp đồng đại lý 2026'))
    return khos, nccs, hhs, khs, {n.username: n for n in nvs}


def _gio(ngay, gio_tu=7, gio_den=21):
    return datetime.combine(ngay, datetime.min.time()) + timedelta(hours=random.randint(gio_tu, gio_den - 1),
                                                                   minutes=random.randint(0, 59))


def _nhap_hang(nv, kho, nccs, hhs, thoi_diem, day_kho=False):
    """Nhap bo sung nhung mat hang ton thap (hoac day kho lan dau)."""
    _DongHo.hien_tai = thoi_diem
    for ncc in nccs.values():
        dong = []
        for hh in hhs.values():
            if hh.nha_cung_cap_id != ncc.id:
                continue
            hmp = hh.loai_hang.ma_loai == 'LH06'
            ton = tonkho.lay_ton_kho(hh.id, kho.id).so_luong_ton
            muc = 120 if hmp else 400
            if day_kho or ton < muc * 0.4:
                ngay_hsd = HANG_HOA[int(hh.ma_hang[2:]) - 1][8]
                dong.append({'hang_hoa_id': hh.id, 'so_luong': muc - ton, 'don_gia': hh.gia_nhap,
                             'han_su_dung': thoi_diem.date() + timedelta(days=ngay_hsd) if ngay_hsd else None})
        if not dong:
            continue
        tong = sum(d['so_luong'] * d['don_gia'] for d in dong)
        tra = tong if day_kho else random.choice([tong, tong, round(tong * 0.5, -3), 0])
        pn = tonkho.nhap_hang(nv, ncc.id, kho.id, dong, tra, thoi_diem.date() + timedelta(days=30))
        pn.ngay_nhap = thoi_diem
        for cn in CongNo.query.filter_by(ma_chung_tu=pn.ma_phieu):
            cn.ngay_phat_sinh = thoi_diem.date()


def _ban_mot_don(nvs, khos, hhs, khs, t, online=False):
    kho = random.choice(list(khos.values()))
    kh = random.choice(khs) if online or random.random() < 0.55 else None
    dai_ly = kh is not None and kh.loai_khach_hang.ma_loai == 'LKH03'
    items = []
    for hh in random.sample(list(hhs.values()), random.randint(2, 7) if dai_ly else random.randint(1, 5)):
        sl = random.randint(10, 40) if dai_ly and hh.loai_hang.ma_loai != 'LH06' else random.randint(1, 3)
        if tonkho.lay_ton_kho(hh.id, kho.id).so_luong_ton >= sl:
            items.append({'hang_hoa_id': hh.id, 'so_luong': sl})
    if not items:
        return None
    nv = random.choice([nvs['nhanvien1'], nvs['nhanvien2']])
    httt = random.choices(['tien_mat', 'the', 'chuyen_khoan'], [6, 2, 2])[0]
    if dai_ly and random.random() < 0.6:
        httt = 'ghi_no'
    diem = min(kh.diem_tich_luy, random.choice([20, 50, 100])) if kh and kh.co_the and kh.diem_tich_luy >= 50 \
        and random.random() < 0.2 else 0
    _DongHo.hien_tai = t
    if online:
        don = banhang.tao_don_hang(kh, items, kho.id, 'online', kh.ho_ten, kh.dia_chi)
        buoc = ['dang_xu_ly', 'dang_giao', 'hoan_thanh']
        for tt in buoc:
            banhang.chuyen_trang_thai(don, tt, nv, httt if httt != 'tien_mat' else 'chuyen_khoan')
    else:
        tam_tinh = sum(banhang.ap_gia(db.session.get(HangHoa, i['hang_hoa_id']), kh)[0] * i['so_luong'] for i in items)
        tien = math.ceil(tam_tinh / 50_000) * 50_000 if httt == 'tien_mat' else 0
        don = banhang.thanh_toan_tai_quay(nv, kh, items, kho.id, httt, diem, tien).don_hang
    # lui thoi gian chung tu ve ngay mo phong
    don.ngay_dat = t
    for i, ls in enumerate(don.lich_sus):
        ls.thoi_gian = t + timedelta(minutes=i * (90 if online else 1))
    hd = don.hoa_don
    hd.ngay_lap = don.lich_sus[-1].thoi_gian
    if kh is not None:
        the = kh.the_than_thiet
        if the is not None and the.chung_tu_dat_dieu_kien == hd.ma_hd:
            the.ngay_lap = hd.ngay_lap
        for ls in LichSuDiem.query.filter_by(khach_hang_id=kh.id, chung_tu=hd.ma_hd):
            ls.ngay = hd.ngay_lap
        for cn in CongNo.query.filter_by(ma_chung_tu=hd.ma_hd):
            cn.ngay_phat_sinh = hd.ngay_lap.date()
            cn.han_thanh_toan = cn.ngay_phat_sinh + timedelta(days=kh.so_ngay_no_ap_dung)
    return don


def _thu_no(nvs, ngay):
    """Khach / NCC tra no dan; mot so chung tu bi bo quen de tao no qua han."""
    for cn in CongNo.query.filter(CongNo.so_tien > CongNo.da_thanh_toan).all():
        tuoi = (ngay - cn.ngay_phat_sinh).days
        if tuoi < 10 or random.random() > 0.06:
            continue
        if cn.doi_tuong == 'khach_hang' and cn.id % 7 == 0:  # chung tu "bi quen" -> qua han
            continue
        so_tien = cn.con_lai if random.random() < 0.8 else round(cn.con_lai / 2, -3)
        if so_tien <= 0 or so_tien > cn.con_lai:
            so_tien = cn.con_lai
        congno.thanh_toan(cn, so_tien, random.choice(['tien_mat', 'chuyen_khoan']), nvs['quanly1'])
        cn.thanh_toans[-1].ngay = _gio(ngay, 8, 17)


def _don_cho_xu_ly(nvs, khos, hhs, khs):
    """Mot so don online hom nay dang o cac trang thai de nhan vien xu ly."""
    bay_gio = datetime.now()
    ds = []
    for i, tt in enumerate(['cho_xu_ly', 'cho_xu_ly', 'cho_xu_ly', 'dang_xu_ly', 'dang_giao', 'da_huy']):
        kh = khs[i]
        kho = list(khos.values())[i % 2]
        items = [{'hang_hoa_id': hh.id, 'so_luong': random.randint(1, 3)} for hh in random.sample(list(hhs.values()), 3)]
        _DongHo.hien_tai = None
        don = banhang.tao_don_hang(kh, items, kho.id, 'online', kh.ho_ten, kh.dia_chi,
                                   'Giao giờ hành chính' if i == 0 else None)
        t = bay_gio - timedelta(hours=6 - i, minutes=random.randint(0, 50))
        don.ngay_dat = t
        if tt == 'da_huy':
            banhang.huy_don_boi_khach(don, kh)
        elif tt != 'cho_xu_ly':
            banhang.chuyen_trang_thai(don, 'dang_xu_ly', nvs['nhanvien1'])
            if tt == 'dang_giao':
                banhang.chuyen_trang_thai(don, 'dang_giao', nvs['nhanvien1'], ghi_chu='Shipper: Anh Tuấn 0908xxx')
        for j, ls in enumerate(don.lich_sus):
            ls.thoi_gian = t + timedelta(minutes=j * 20)
        ds.append(don)
    return ds


def tao_du_lieu(app, so_ngay=SO_NGAY_MO_PHONG):
    random.seed(16)
    goc = (helpers.datetime, tonkho.kiem_tra_canh_bao_ton_kho, congno.kiem_tra_canh_bao_cong_no)
    # tat canh bao trong luc mo phong (chay 1 lan o cuoi) va gia lap ngay cho ma chung tu
    helpers.datetime = _DongHo
    tonkho.kiem_tra_canh_bao_ton_kho = congno.kiem_tra_canh_bao_cong_no = lambda: 0
    try:
        with app.test_request_context():
            khos, nccs, hhs, khs, nvs = _danh_muc()
            bat_dau = date.today() - timedelta(days=so_ngay)
            for kho in khos.values():
                _nhap_hang(nvs['kho1'], kho, nccs, hhs, _gio(bat_dau, 7, 9), day_kho=True)
            db.session.commit()
            so_don = 0
            for d in range(so_ngay - 1, 0, -1):
                ngay = date.today() - timedelta(days=d)
                if d % 20 == 0:
                    for kho in khos.values():
                        _nhap_hang(nvs['kho1'], kho, nccs, hhs, _gio(ngay, 6, 8))
                tien_trien = 1 - d / so_ngay
                so_luong = random.randint(2, 4) + int(4 * tien_trien) + (2 if ngay.weekday() >= 5 else 0)
                for _ in range(so_luong):
                    if _ban_mot_don(nvs, khos, hhs, khs, _gio(ngay), online=random.random() < 0.12):
                        so_don += 1
                _thu_no(nvs, ngay)
                db.session.commit()
            _don_cho_xu_ly(nvs, khos, hhs, khs)
            moi = KhachHang(ma_kh=f'KH{len(khs) + 1:04d}', ho_ten='Trương Mỹ Linh', dien_thoai='0911222333',
                            dia_chi='9 Pasteur, Q.3, TP.HCM', loai_khach_hang=khs[1].loai_khach_hang,
                            email='mylinh@example.com', tong_mua=0, diem_tich_luy=0, trang_thai=True)
            moi.set_password('123456')
            db.session.add(moi)
            # nguong rieng cho hang ban chay / hang cong kenh de minh hoa canh bao ton kho
            for ma in ('HH010', 'HH005'):
                for tk in hhs[ma].ton_khos:
                    tk.muc_toi_thieu = max(tk.muc_toi_thieu, tk.so_luong_ton + 50)
            # HSD cua lo hang dang ban: phan lon con han, vai mat hang sap / da het han de minh hoa kiosk
            for i, hh in enumerate(hhs.values()):
                hsd = HANG_HOA[i][8]
                hh.han_su_dung = date.today() + timedelta(days=random.randint(hsd // 3, hsd)) if hsd else None
            hhs['HH003'].han_su_dung = date.today() + timedelta(days=2)
            hhs['HH002'].han_su_dung = date.today() + timedelta(days=6)
            hhs['HH019'].han_su_dung = date.today() - timedelta(days=3)
            for tk in hhs['HH022'].ton_khos:
                tk.muc_toi_da = max(10, tk.so_luong_ton - 20)
            db.session.commit()
            helpers.datetime, tonkho.kiem_tra_canh_bao_ton_kho, congno.kiem_tra_canh_bao_cong_no = goc
            # han muc rieng thap cho 1 dai ly de minh hoa canh bao no vuot muc
            kh = KhachHang.query.filter_by(dien_thoai='0903111222').first()
            no = congno.tong_no_khach_hang(kh.id)
            if no > 0:
                kh.han_muc_no = max(500_000, round(no * 0.7, -5))
            so_canh_bao = thongbao.kiem_tra_tat_ca()
            db.session.commit()
            print(f'Da tao du lieu mau: {len(hhs)} mat hang, {KhachHang.query.count()} khach hang, {so_don} don hoan thanh '
                  f'trong {so_ngay} ngay, {TheThanhThiet.query.count()} the than thiet, '
                  f'{CongNo.query.count()} chung tu cong no, {so_canh_bao} canh bao.')
    finally:
        helpers.datetime, tonkho.kiem_tra_canh_bao_ton_kho, congno.kiem_tra_canh_bao_cong_no = goc


if __name__ == '__main__':
    from config import Config

    class _SeedConfig(Config):
        SCHEDULER_ENABLED = False

    app = create_app(_SeedConfig)
    with app.app_context():
        if '--reset' in sys.argv:
            db.drop_all()
            db.create_all()
        elif NguoiDung.query.first() is not None:
            print('CSDL da co du lieu. Dung "python seed.py --reset" de tao lai.')
            sys.exit(0)
    tao_du_lieu(app)
