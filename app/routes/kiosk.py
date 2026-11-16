"""Kiosk tra cuu tai sieu thi: khong can dang nhap, tra cuu gia, HSD, thong tin co ban (SD10)."""
from flask import Blueprint, render_template, request, jsonify

from app.extensions import db
from app.models import HangHoa, LoaiHangHoa

bp = Blueprint('kiosk', __name__)


@bp.route('/')
def index():
    return render_template('kiosk/index.html', loais=LoaiHangHoa.query.order_by(LoaiHangHoa.ten_loai).all())


@bp.route('/api/tra-cuu')
def tra_cuu():
    tu_khoa = request.args.get('q', '').strip()
    loai = request.args.get('loai', type=int)
    q = HangHoa.query.filter_by(trang_thai=True)
    if tu_khoa:
        q = q.filter(db.or_(HangHoa.ma_vach == tu_khoa, HangHoa.ma_hang == tu_khoa,
                            HangHoa.ten_hang.ilike(f'%{tu_khoa}%')))
    elif loai:
        q = q.filter_by(loai_hang_id=loai)
    else:
        return jsonify([])
    ket_qua = []
    for hh in q.order_by(HangHoa.ten_hang).limit(40):
        ngay = hh.so_ngay_con_han
        ket_qua.append({
            'ten': hh.ten_hang, 'ma_vach': hh.ma_vach, 'gia': hh.gia_ban, 'dvt': hh.don_vi_tinh,
            'loai': hh.loai_hang.ten_loai if hh.loai_hang else '', 'xuat_xu': hh.xuat_xu or '',
            'ncc': hh.nha_cung_cap.ten_ncc if hh.nha_cung_cap else '', 'mo_ta': hh.mo_ta or '',
            'hsd': hh.han_su_dung.strftime('%d/%m/%Y') if hh.han_su_dung else None, 'so_ngay_con_han': ngay,
            'con_hang': hh.tong_ton > 0,
        })
    return jsonify(ket_qua)
