from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for

from app.models import ThongBao, DonHang
from app.services import thongke
from app.utils.decorators import nhan_vien_required, la_khach_hang

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def trang_chu():
    if la_khach_hang():
        return redirect(url_for('portal.cua_hang'))
    return redirect(url_for('dashboard.index'))


@bp.route('/tong-quan')
@nhan_vien_required
def index():
    hom_nay = date.today()
    bieu_do = thongke.doanh_thu_theo_ky('ngay', hom_nay - timedelta(days=6), hom_nay)
    return render_template(
        'dashboard/index.html',
        tq=thongke.tong_quan_hom_nay(),
        bieu_do=bieu_do,
        canh_baos=ThongBao.query.filter_by(da_xu_ly=False).order_by(ThongBao.ngay_tao.desc()).limit(8).all(),
        don_moi=DonHang.query.filter_by(trang_thai='cho_xu_ly').order_by(DonHang.ngay_dat.desc()).limit(6).all(),
        top_hang=thongke.theo_hang_hoa(hom_nay - timedelta(days=29), hom_nay)[:5],
    )
