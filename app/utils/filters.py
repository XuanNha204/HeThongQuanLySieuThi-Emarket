from datetime import date, datetime

from flask import render_template


def vnd(v):
    if v is None:
        return ''
    return f"{v:,.0f}".replace(',', '.') + ' đ'


def so(v):
    if v is None:
        return ''
    return f"{v:,.0f}".replace(',', '.')


def ngay(v):
    return v.strftime('%d/%m/%Y') if isinstance(v, (date, datetime)) else (v or '')


def ngay_gio(v):
    return v.strftime('%d/%m/%Y %H:%M') if isinstance(v, datetime) else ngay(v)


def register(app):
    from app.models import CHUC_NANG, QUYEN, VAI_TRO, TRANG_THAI_DON, HINH_THUC_TT
    from app.utils.decorators import la_nhan_vien, la_khach_hang

    app.jinja_env.filters.update(vnd=vnd, so=so, ngay=ngay, ngay_gio=ngay_gio)
    app.jinja_env.globals.update(
        CHUC_NANG=CHUC_NANG, QUYEN=QUYEN, VAI_TRO=VAI_TRO, TRANG_THAI_DON=TRANG_THAI_DON,
        HINH_THUC_TT=HINH_THUC_TT, la_nhan_vien=la_nhan_vien, la_khach_hang=la_khach_hang,
        hom_nay=date.today,
    )

    @app.errorhandler(403)
    def cam(e):
        return render_template('loi.html', ma=403, thong_bao='Bạn không có quyền thực hiện chức năng này.'), 403

    @app.errorhandler(404)
    def khong_thay(e):
        return render_template('loi.html', ma=404, thong_bao='Không tìm thấy trang hoặc dữ liệu yêu cầu.'), 404
