"""Kiem thu tich hop eMarket (Flask test client, CSDL SQLite trong bo nho).

    venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""
import io
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

from flask import g
from flask.testing import FlaskClient
from openpyxl import Workbook, load_workbook

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seed  # noqa: E402
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (HangHoa, KhachHang, Kho, NhaCungCap, DonHang, HoaDon, CongNo, ThongBao, TonKho,  # noqa: E402
                        PhieuNhap, NguoiDung, GiaBanTheoKH, LoaiKhachHang)
from app.services import banhang  # noqa: E402
from config import TestConfig  # noqa: E402


class _Client(FlaskClient):
    """App context duoc giu suot bai test nen g dung chung giua cac request: xoa user da nap cua request truoc."""

    def open(self, *args, **kwargs):
        g.pop('_login_user', None)
        return super().open(*args, **kwargs)


class CoSo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)
        cls.app.test_client_class = _Client
        cls.ctx = cls.app.app_context()
        cls.ctx.push()
        db.drop_all()
        db.create_all()
        seed.tao_du_lieu(cls.app, 30)

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.ctx.pop()

    def setUp(self):
        self.c = self.app.test_client()

    def dang_nhap(self, u='admin', p='admin123'):
        r = self.c.post('/dang-nhap', data={'username': u, 'password': p})
        self.assertEqual(r.status_code, 302, r.data[:300])

    def dang_nhap_kh(self, dt='0901234567', p='123456'):
        r = self.c.post('/khach/dang-nhap', data={'dien_thoai': dt, 'mat_khau': p})
        self.assertEqual(r.status_code, 302)

    def ok(self, url, ma=200):
        r = self.c.get(url)
        self.assertEqual(r.status_code, ma, f'{url}: {r.data[:500]}')
        return r

    @staticmethod
    def kho():
        return Kho.query.order_by(Kho.id).first()

    @staticmethod
    def hang(ma='HH010'):
        return HangHoa.query.filter_by(ma_hang=ma).first()

    @staticmethod
    def ton(hh, kho):
        db.session.expire_all()
        return TonKho.query.filter_by(hang_hoa_id=hh.id, kho_id=kho.id).first().so_luong_ton


class TestTrang(CoSo):
    """Moi trang deu mo duoc voi dung vai tro; trang bi chan dung quyen."""

    TRANG_NV = ['/tong-quan', '/danh-muc/nha-cung-cap', '/danh-muc/loai-hang', '/danh-muc/hang-hoa', '/danh-muc/hang-hoa?q=sữa',
                '/danh-muc/loai-khach-hang', '/danh-muc/kho', '/danh-muc/hang-hoa/them', '/danh-muc/hang-hoa/1/sua',
                '/danh-muc/hang-hoa/1/in-ma-vach', '/danh-muc/hang-hoa/in-ma-vach?hh=1&hh=2&chuan=code128',
                '/khach-hang/danh-sach', '/khach-hang/1', '/khach-hang/the-than-thiet', '/ban-hang/pos',
                '/ban-hang/hoa-don', '/ban-hang/hoa-don?q=HD&tu=2020-01-01', '/ban-hang/hoa-don/1/in',
                '/ban-hang/don-hang', '/ban-hang/don-hang?nguon=tat_ca&trang_thai=hoan_thanh',
                '/ban-hang/don-hang/1', '/ban-hang/gia-ban', '/ban-hang/gia-ban?kh_id=10', '/ton-kho/',
                '/ton-kho/?tinh_trang=thieu', '/ton-kho/?tinh_trang=vuot&kho_id=1', '/ton-kho/phieu-nhap',
                '/ton-kho/phieu-nhap/them', '/ton-kho/phieu-nhap/1', '/cong-no/',
                '/cong-no/?doi_tuong=nha_cung_cap&trang_thai=tat_ca', '/cong-no/?trang_thai=qua_han',
                '/cong-no/tong-hop', '/cong-no/1', '/thong-ke/', '/thong-ke/?loai=thang', '/thong-ke/?loai=nam',
                '/thong-ke/?loai=hang_hoa', '/thong-ke/?loai=ncc', '/he-thong/nguoi-dung',
                '/he-thong/nguoi-dung/them', '/he-thong/nguoi-dung/2/sua', '/he-thong/thong-bao',
                '/he-thong/thong-bao?xem=da_xu_ly', '/he-thong/thong-bao?loai=no_qua_han', '/he-thong/sao-luu',
                '/he-thong/doi-mat-khau']
    TRANG_CONG_KHAI = ['/kiosk/', '/kiosk/api/tra-cuu?q=sữa', '/khach/', '/khach/?q=mì', '/khach/?loai=1',
                       '/khach/gio-hang', '/khach/dang-nhap', '/khach/dang-ky', '/dang-nhap']

    def test_admin_mo_moi_trang(self):
        self.dang_nhap()
        for url in self.TRANG_NV:
            with self.subTest(url=url):
                self.ok(url)

    def test_trang_cong_khai(self):
        for url in self.TRANG_CONG_KHAI:
            with self.subTest(url=url):
                self.ok(url)
        hh = self.hang()
        r = self.ok(f'/danh-muc/ma-vach/ean13/{hh.ma_vach}.svg')
        self.assertIn(b'<svg', r.data)
        self.ok('/danh-muc/ma-vach/ean13/123.svg', 404)

    def test_chua_dang_nhap_bi_chuyen_huong(self):
        for url in ['/tong-quan', '/ban-hang/pos', '/thong-ke/', '/khach/tai-khoan']:
            with self.subTest(url=url):
                self.assertEqual(self.c.get(url).status_code, 302)

    def test_phan_quyen_theo_vai_tro(self):
        self.dang_nhap('kho1', '123456')
        self.ok('/ton-kho/')
        self.ok('/ton-kho/phieu-nhap/them')
        self.ok('/ban-hang/pos', 403)
        self.ok('/he-thong/nguoi-dung', 403)
        self.c.post('/dang-xuat')
        self.dang_nhap('nhanvien1', '123456')
        self.ok('/ban-hang/pos')
        self.ok('/ton-kho/phieu-nhap/them', 403)
        self.ok('/he-thong/nguoi-dung', 403)
        self.ok('/he-thong/sao-luu', 403)

    def test_khach_hang_khong_vao_trang_quan_tri(self):
        self.dang_nhap_kh()
        self.assertNotEqual(self.c.get('/ban-hang/pos').status_code, 200)
        self.ok('/khach/tai-khoan')
        self.ok('/khach/don-hang')

    def test_xuat_excel(self):
        self.dang_nhap()
        for url in ['/danh-muc/hang-hoa/xuat-excel', '/danh-muc/nha-cung-cap/mau-excel', '/khach-hang/danh-sach/xuat-excel',
                    '/ban-hang/hoa-don?xuat=1', '/ton-kho/?xuat=1', '/cong-no/?xuat=1', '/thong-ke/?loai=thang&xuat=1',
                    '/ton-kho/phieu-nhap/mau-excel']:
            with self.subTest(url=url):
                r = self.ok(url)
                wb = load_workbook(io.BytesIO(r.data))
                self.assertGreaterEqual(wb.active.max_row, 1)


class TestNghiepVu(CoSo):
    def test_ban_hang_tai_quay_json(self):
        self.dang_nhap('nhanvien1', '123456')
        kho, hh = self.kho(), self.hang('HH009')
        ton = self.ton(hh, kho)
        r = self.c.get(f'/ban-hang/api/hang-hoa?q={hh.ma_vach}&kho_id={kho.id}')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(x['ma_vach'] == hh.ma_vach and x['ton'] > 0 for x in r.get_json()))
        r = self.c.post('/ban-hang/pos/thanh-toan', json={'kho_id': kho.id, 'hinh_thuc_tt': 'tien_mat',
                                                          'tien_khach_dua': 100000,
                                                          'items': [{'hang_hoa_id': hh.id, 'so_luong': 3}]})
        d = r.get_json()
        self.assertTrue(d['ok'], d)
        self.assertEqual(d['tien_thoi'], 100000 - 3 * hh.gia_ban)
        self.assertEqual(self.ton(hh, kho), ton - 3)
        self.ok(d['url_in'])
        # thieu tien, vuot ton kho, khach le ghi no -> loi nghiep vu
        for body in [{'hinh_thuc_tt': 'tien_mat', 'tien_khach_dua': 1000, 'items': [{'hang_hoa_id': hh.id, 'so_luong': 3}]},
                     {'hinh_thuc_tt': 'the', 'items': [{'hang_hoa_id': hh.id, 'so_luong': 10 ** 6}]},
                     {'hinh_thuc_tt': 'ghi_no', 'items': [{'hang_hoa_id': hh.id, 'so_luong': 1}]}]:
            r = self.c.post('/ban-hang/pos/thanh-toan', json={'kho_id': kho.id, **body})
            self.assertEqual(r.status_code, 400)
            self.assertFalse(r.get_json()['ok'])
        self.assertEqual(self.ton(hh, kho), ton - 3)

    def test_lap_the_tu_dong_va_tich_diem(self):
        kh = KhachHang(ma_kh='KHT001', ho_ten='Khách thử', dien_thoai='0999000001')
        db.session.add(kh)
        db.session.commit()
        self.dang_nhap('nhanvien1', '123456')
        kho, hh = self.kho(), self.hang('HH021')  # 72.000d
        r = self.c.post('/ban-hang/pos/thanh-toan', json={'kho_id': kho.id, 'kh_id': kh.id, 'hinh_thuc_tt': 'the',
                                                          'items': [{'hang_hoa_id': hh.id, 'so_luong': 1}]})
        self.assertFalse(r.get_json()['co_the_moi'])  # 72.000 < 100.000
        r = self.c.post('/ban-hang/pos/thanh-toan', json={'kho_id': kho.id, 'kh_id': kh.id, 'hinh_thuc_tt': 'the',
                                                          'items': [{'hang_hoa_id': hh.id, 'so_luong': 2}]})
        d = r.get_json()
        self.assertTrue(d['co_the_moi'], d)  # 144.000 >= 100.000 trong 1 lan mua
        db.session.expire_all()
        kh = db.session.get(KhachHang, kh.id)
        self.assertIsNotNone(kh.the_than_thiet)
        self.assertEqual(kh.diem_tich_luy, 14)  # 144.000 / 10.000
        # dung diem: 10 diem = 1.000d
        r = self.c.post('/ban-hang/pos/thanh-toan', json={'kho_id': kho.id, 'kh_id': kh.id, 'hinh_thuc_tt': 'the',
                                                          'diem_su_dung': 10,
                                                          'items': [{'hang_hoa_id': hh.id, 'so_luong': 1}]})
        self.assertEqual(r.get_json()['tong'], 72000 - 1000)

    def test_gia_ban_theo_khach_hang(self):
        dai_ly = KhachHang.query.filter_by(dien_thoai='0283999888').first()
        vip = KhachHang.query.filter_by(dien_thoai='0901234567').first()
        hh = self.hang('HH005')
        self.assertEqual(banhang.ap_gia(hh, dai_ly)[0], 9000)                  # gia rieng
        self.assertEqual(banhang.ap_gia(hh, vip)[0], round(10500 * 0.97, -2))  # chiet khau loai KH
        self.assertEqual(banhang.ap_gia(hh, None)[0], 10500)                   # gia niem yet
        self.dang_nhap()
        r = self.c.post('/ban-hang/gia-ban', data={'kh_id': vip.id, 'hang_hoa_id': hh.id, 'gia_ban': 9900})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(banhang.ap_gia(hh, vip)[0], 9900)
        gb = GiaBanTheoKH.query.filter_by(khach_hang_id=vip.id, hang_hoa_id=hh.id).first()
        self.c.post(f'/ban-hang/gia-ban/{gb.id}/xoa')
        self.assertEqual(banhang.ap_gia(hh, vip)[0], round(10500 * 0.97, -2))

    def test_dat_hang_online_den_hoan_thanh(self):
        kho, hh = self.kho(), self.hang('HH012')
        ton = self.ton(hh, kho)
        self.dang_nhap_kh('0934567890')
        self.c.post('/khach/gio-hang/them', data={'hang_hoa_id': hh.id, 'so_luong': 2})
        self.c.post('/khach/gio-hang/them', data={'hang_hoa_id': self.hang('HH001').id})
        r = self.ok('/khach/gio-hang')
        self.assertIn(hh.ten_hang.encode(), r.data)
        self.c.post('/khach/gio-hang', data={f'sl_{hh.id}': 4, 'xoa': self.hang('HH001').id})
        r = self.c.post('/khach/dat-hang', data={'kho_id': kho.id, 'dia_chi_giao': '1 Lê Duẩn'})
        self.assertEqual(r.status_code, 302)
        don = DonHang.query.order_by(DonHang.id.desc()).first()
        self.assertEqual((don.trang_thai, len(don.chi_tiets), don.chi_tiets[0].so_luong), ('cho_xu_ly', 1, 4))
        self.ok(f'/khach/don-hang/{don.id}')
        self.assertEqual(self.ton(hh, kho), ton)  # chua tru kho khi moi dat
        self.c.post('/khach/dang-xuat') if False else None
        c_nv = self.app.test_client()
        c_nv.post('/dang-nhap', data={'username': 'nhanvien1', 'password': '123456'})
        for tt in ['dang_xu_ly', 'dang_giao', 'hoan_thanh']:
            r = c_nv.post(f'/ban-hang/don-hang/{don.id}/trang-thai', data={'trang_thai': tt, 'hinh_thuc_tt': 'tien_mat'})
            self.assertEqual(r.status_code, 302)
        db.session.expire_all()
        don = db.session.get(DonHang, don.id)
        self.assertEqual(don.trang_thai, 'hoan_thanh')
        self.assertIsNotNone(don.hoa_don)
        self.assertEqual([l.trang_thai for l in don.lich_sus], ['cho_xu_ly', 'dang_xu_ly', 'dang_giao', 'hoan_thanh'])
        self.assertEqual(self.ton(hh, kho), ton - 4)
        # khong the chuyen tiep tu trang thai ket thuc
        c_nv.post(f'/ban-hang/don-hang/{don.id}/trang-thai', data={'trang_thai': 'da_huy'})
        db.session.expire_all()
        self.assertEqual(db.session.get(DonHang, don.id).trang_thai, 'hoan_thanh')

    def test_khach_huy_don(self):
        self.dang_nhap_kh('0912345678')
        self.c.post('/khach/gio-hang/them', data={'hang_hoa_id': self.hang('HH010').id})
        self.c.post('/khach/dat-hang', data={'kho_id': self.kho().id, 'dia_chi_giao': 'abc'})
        don = DonHang.query.order_by(DonHang.id.desc()).first()
        self.c.post(f'/khach/don-hang/{don.id}/huy')
        db.session.expire_all()
        self.assertEqual(db.session.get(DonHang, don.id).trang_thai, 'da_huy')
        # khach khac khong xem duoc don
        c2 = self.app.test_client()
        c2.post('/khach/dang-nhap', data={'dien_thoai': '0901234567', 'mat_khau': '123456'})
        self.assertEqual(c2.get(f'/khach/don-hang/{don.id}').status_code, 404)

    def test_dang_ky_khach_hang(self):
        r = self.c.post('/khach/dang-ky', data={'ho_ten': 'Người mới', 'dien_thoai': '0988777666',
                                                'mat_khau': 'abcdef', 'nhap_lai': 'abcdef'})
        self.assertEqual(r.status_code, 302)
        self.ok('/khach/tai-khoan')

    def test_nhap_hang_form_va_cong_no_ncc(self):
        self.dang_nhap('kho1', '123456')
        kho, hh = self.kho(), self.hang('HH015')
        ncc = hh.nha_cung_cap
        ton = self.ton(hh, kho)
        hsd = (date.today() + timedelta(days=400)).isoformat()
        r = self.c.post('/ton-kho/phieu-nhap/them', data={
            'nha_cung_cap_id': ncc.id, 'kho_id': kho.id, 'hang_hoa_id': [hh.id], 'so_luong': ['100'],
            'don_gia': ['30000'], 'han_su_dung': [hsd], 'da_thanh_toan': '1000000'})
        self.assertEqual(r.status_code, 302, r.data[:300])
        self.assertEqual(self.ton(hh, kho), ton + 100)
        pn = PhieuNhap.query.order_by(PhieuNhap.id.desc()).first()
        cn = CongNo.query.filter_by(ma_chung_tu=pn.ma_phieu).one()
        self.assertEqual((cn.doi_tuong, cn.so_tien), ('nha_cung_cap', 2_000_000))
        self.assertEqual(cn.han_thanh_toan, date.today() + timedelta(days=30))
        db.session.expire_all()
        self.assertEqual(self.hang('HH015').han_su_dung.isoformat(), hsd)
        # tra no NCC
        c = self.app.test_client()
        c.post('/dang-nhap', data={'username': 'admin', 'password': 'admin123'})
        c.post(f'/cong-no/{cn.id}', data={'so_tien': 2_000_000, 'hinh_thuc': 'chuyen_khoan'})
        db.session.expire_all()
        self.assertEqual(db.session.get(CongNo, cn.id).con_lai, 0)
        self.assertEqual(db.session.get(PhieuNhap, pn.id).da_thanh_toan, 3_000_000)

    def test_nhap_hang_tu_excel(self):
        self.dang_nhap('kho1', '123456')
        kho, h1, h2 = self.kho(), self.hang('HH016'), self.hang('HH017')
        t1, t2 = self.ton(h1, kho), self.ton(h2, kho)
        wb = Workbook()
        ws = wb.active
        ws.append(['Mã hàng *', 'Số lượng *', 'Đơn giá *', 'Hạn sử dụng'])
        ws.append(['HH016', 20, 14000, '31/12/2027'])
        ws.append([h2.ma_vach, 30, 12000, None])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = self.c.post('/ton-kho/phieu-nhap/nhap-excel', data={
            'nha_cung_cap_id': h1.nha_cung_cap_id, 'kho_id': kho.id, 'da_thanh_toan': '0',
            'file': (buf, 'pn.xlsx')}, content_type='multipart/form-data')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/ton-kho/phieu-nhap/', r.headers['Location'])
        self.assertEqual((self.ton(h1, kho), self.ton(h2, kho)), (t1 + 20, t2 + 30))

    def test_canh_bao_ton_kho_min_max(self):
        self.dang_nhap()
        kho, hh = self.kho(), self.hang('HH013')
        tk = TonKho.query.filter_by(hang_hoa_id=hh.id, kho_id=kho.id).first()
        r = self.c.post(f'/ton-kho/{tk.id}/nguong', data={'muc_toi_thieu': tk.so_luong_ton + 1, 'muc_toi_da': 5000})
        self.assertEqual(r.status_code, 302)
        self.c.post('/he-thong/thong-bao/kiem-tra')
        self.assertIsNotNone(ThongBao.query.filter_by(khoa=f'ton_thieu:{tk.id}', da_xu_ly=False).first())
        self.c.post(f'/ton-kho/{tk.id}/nguong', data={'muc_toi_thieu': 0, 'muc_toi_da': 1})
        self.c.post('/he-thong/thong-bao/kiem-tra')
        db.session.expire_all()
        self.assertIsNone(ThongBao.query.filter_by(khoa=f'ton_thieu:{tk.id}', da_xu_ly=False).first())
        self.assertIsNotNone(ThongBao.query.filter_by(khoa=f'ton_vuot:{tk.id}', da_xu_ly=False).first())
        # nguong khong hop le
        self.c.post(f'/ton-kho/{tk.id}/nguong', data={'muc_toi_thieu': 50, 'muc_toi_da': 10})
        db.session.expire_all()
        self.assertEqual(db.session.get(TonKho, tk.id).muc_toi_da, 1)

    def test_ghi_no_qua_han_va_vuot_han_muc(self):
        kh = KhachHang.query.filter_by(dien_thoai='0283999888').first()
        self.dang_nhap('nhanvien1', '123456')
        kho, hh = self.kho(), self.hang('HH022')
        r = self.c.post('/ban-hang/pos/thanh-toan', json={'kho_id': kho.id, 'kh_id': kh.id, 'hinh_thuc_tt': 'ghi_no',
                                                          'items': [{'hang_hoa_id': hh.id, 'so_luong': 2}]})
        d = r.get_json()
        self.assertTrue(d['ok'], d)
        cn = CongNo.query.filter_by(ma_chung_tu=d['ma_hd']).one()
        self.assertEqual(cn.han_thanh_toan, date.today() + timedelta(days=30))
        cn.han_thanh_toan = date.today() - timedelta(days=1)
        kh.han_muc_no = 1000
        db.session.commit()
        c = self.app.test_client()
        c.post('/dang-nhap', data={'username': 'admin', 'password': 'admin123'})
        c.post('/he-thong/thong-bao/kiem-tra')
        self.assertIsNotNone(ThongBao.query.filter_by(khoa=f'no_qua_han:{cn.id}', da_xu_ly=False).first())
        self.assertIsNotNone(ThongBao.query.filter_by(khoa=f'no_vuot_muc:{kh.id}', da_xu_ly=False).first())
        self.assertIn('VƯỢT MỨC'.encode(), c.get('/cong-no/tong-hop').data)
        # thu qua so con no -> tu choi; thu du -> het canh bao qua han
        c.post(f'/cong-no/{cn.id}', data={'so_tien': cn.con_lai + 1000, 'hinh_thuc': 'tien_mat'})
        db.session.expire_all()
        self.assertGreater(db.session.get(CongNo, cn.id).con_lai, 0)
        c.post(f'/cong-no/{cn.id}', data={'so_tien': db.session.get(CongNo, cn.id).con_lai, 'hinh_thuc': 'tien_mat'})
        db.session.expire_all()
        self.assertIsNone(ThongBao.query.filter_by(khoa=f'no_qua_han:{cn.id}', da_xu_ly=False).first())
        kh.han_muc_no = None
        db.session.commit()

    def test_bao_cao(self):
        self.dang_nhap('quanly1', '123456')
        tong_hd = sum(h.tong_tien for h in HoaDon.query.filter(
            db.func.date(HoaDon.ngay_lap) >= (date.today() - timedelta(days=29)).isoformat()).all())
        for loai in ['ngay', 'thang', 'nam', 'hang_hoa', 'ncc']:
            with self.subTest(loai=loai):
                r = self.ok(f'/thong-ke/?loai={loai}&xuat=1')
                ws = load_workbook(io.BytesIO(r.data)).active
                self.assertGreater(ws.max_row, 2)
        r = self.ok('/thong-ke/?loai=ngay&xuat=1')
        ws = load_workbook(io.BytesIO(r.data)).active
        hang = [list(x) for x in ws.iter_rows(values_only=True)]
        cot_dt = next(i for i, v in enumerate(next(h for h in hang if h and 'Doanh thu' in [str(x) for x in h]))
                      if str(v) == 'Doanh thu')
        dong_so = [h for h in hang if h and isinstance(h[cot_dt], (int, float))]
        self.assertAlmostEqual(sum(h[cot_dt] for h in dong_so[:-1] if not str(h[0]).startswith('Tổng')),
                               tong_hd, delta=1)

    def test_kiosk_tra_cuu(self):
        hh = self.hang('HH003')
        d = self.c.get(f'/kiosk/api/tra-cuu?q={hh.ma_vach}').get_json()
        self.assertEqual(len(d), 1)
        self.assertEqual((d[0]['ten'], d[0]['gia'], d[0]['hsd']), (hh.ten_hang, hh.gia_ban,
                                                                  hh.han_su_dung.strftime('%d/%m/%Y')))
        self.assertEqual(self.c.get('/kiosk/api/tra-cuu?q=khong-co-hang-nay').get_json(), [])
        self.assertGreater(len(self.c.get(f'/kiosk/api/tra-cuu?loai={hh.loai_hang_id}').get_json()), 1)

    def test_crud_danh_muc_va_excel(self):
        self.dang_nhap()
        r = self.c.post('/danh-muc/hang-hoa/them', data={
            'ma_hang': 'HH900', 'ten_hang': 'Hàng thử', 'chuan_ma_vach': 'ean13', 'don_vi_tinh': 'Cái',
            'gia_ban': '15000', 'gia_nhap': '10000', 'trang_thai': 'on'})
        self.assertEqual(r.status_code, 302, r.data[:500])
        hh = HangHoa.query.filter_by(ma_hang='HH900').one()
        self.assertEqual(len(hh.ma_vach), 13)
        self.assertEqual(TonKho.query.filter_by(hang_hoa_id=hh.id).count(), Kho.query.count())
        # trung ma -> bao loi, khong tao them
        self.c.post('/danh-muc/hang-hoa/them', data={'ma_hang': 'HH900', 'ten_hang': 'x', 'chuan_ma_vach': 'ean13',
                                                     'don_vi_tinh': 'Cái', 'gia_ban': '1'})
        self.assertEqual(HangHoa.query.filter_by(ma_hang='HH900').count(), 1)
        # nhap excel nha cung cap
        wb = load_workbook(io.BytesIO(self.ok('/danh-muc/nha-cung-cap/mau-excel').data))
        ws = wb.active
        tieu_de = [c.value for c in ws[1]]
        ws.delete_rows(2, ws.max_row)
        dong = {t: '' for t in tieu_de}
        dong.update({tieu_de[0]: 'NCC99', tieu_de[1]: 'NCC nhập từ Excel'})
        ws.append([dong[t] for t in tieu_de])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        r = self.c.post('/danh-muc/nha-cung-cap/nhap-excel', data={'file': (buf, 'ncc.xlsx')},
                        content_type='multipart/form-data')
        self.assertEqual(r.status_code, 302)
        self.assertIsNotNone(NhaCungCap.query.filter_by(ma_ncc='NCC99').first())
        # xoa hang da phat sinh giao dich -> chuyen ngung kinh doanh
        hh1 = self.hang('HH001')
        self.c.post(f'/danh-muc/hang-hoa/{hh1.id}/xoa')
        db.session.expire_all()
        self.assertFalse(self.hang('HH001').trang_thai)
        self.hang('HH001').trang_thai = True
        db.session.commit()

    def test_phan_quyen_chi_tiet(self):
        self.dang_nhap()
        r = self.c.post('/he-thong/nguoi-dung/them', data={
            'username': 'nvtest', 'ho_ten': 'NV thử', 'password': '123456', 'vai_tro': 'ban_hang',
            'trang_thai': 'on', 'q_bao_cao_xem': 'on'})
        self.assertEqual(r.status_code, 302, r.data[:400])
        nd = NguoiDung.query.filter_by(username='nvtest').one()
        self.assertTrue(nd.co_quyen('bao_cao', 'xem'))
        self.assertFalse(nd.co_quyen('hoa_don', 'them'))
        c = self.app.test_client()
        c.post('/dang-nhap', data={'username': 'nvtest', 'password': '123456'})
        self.assertEqual(c.get('/thong-ke/').status_code, 200)
        self.assertEqual(c.get('/ban-hang/pos').status_code, 403)
        self.assertEqual(c.post('/ban-hang/pos/thanh-toan', json={}).status_code, 403)

    def test_sao_luu(self):
        thu_muc = tempfile.mkdtemp()
        self.app.config['BACKUP_DIR'] = thu_muc
        self.dang_nhap()
        r = self.c.post('/he-thong/sao-luu', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Sao lưu thất bại'.encode(), r.data)  # CSDL trong bo nho -> bao loi than thien, khong crash


class TestSaoLuuFile(unittest.TestCase):
    def test_sao_luu_csdl_file(self):
        thu_muc = tempfile.mkdtemp()

        class C(TestConfig):
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(thu_muc, 'db.sqlite').replace('\\', '/')
            BACKUP_DIR = os.path.join(thu_muc, 'bk')
        app = create_app(C)
        with app.app_context():
            db.create_all()
            db.session.add(Kho(ma_kho='K1', ten_kho='Kho 1'))
            db.session.commit()
            from app.services import backup
            tep = backup.duong_dan(backup.sao_luu())
            self.assertTrue(os.path.exists(tep))
            self.assertGreater(os.path.getsize(tep), 0)
            db.session.remove()
            db.engine.dispose()


if __name__ == '__main__':
    unittest.main()
