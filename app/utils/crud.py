"""Bo CRUD dung chung cho cac danh muc (SD12): danh sach, tim kiem, them, sua, xoa, nhap/xuat Excel."""
from datetime import date

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.services import LoiNghiepVu, excel
from app.utils.decorators import quyen_required
from app.utils.helpers import so_thuc, doc_ngay


class Truong:
    """Mo ta 1 truong nhap lieu."""

    def __init__(self, ten, nhan, kieu='text', bat_buoc=False, model=None, cot_ma=None, hien_thi=None,
                 chon=None, min=None, goi_y=None, excel=True, rong=6):
        self.ten, self.nhan, self.kieu, self.bat_buoc = ten, nhan, kieu, bat_buoc
        self.model, self.cot_ma, self.hien_thi = model, cot_ma, hien_thi
        self.chon, self.min, self.goi_y, self.excel, self.rong = chon, min, goi_y, excel, rong

    @property
    def nhan_excel(self):
        return self.nhan + (' *' if self.bat_buoc else '')

    def lua_chon(self):
        """Danh sach (gia tri, nhan) cho o chon."""
        if self.chon:
            return list(self.chon.items())
        q = self.model.query
        if hasattr(self.model, 'trang_thai'):
            q = q.filter_by(trang_thai=True)
        return [(o.id, str(o)) for o in q.order_by(getattr(self.model, self.cot_ma))]


def lay_thuoc_tinh(obj, duong_dan):
    for p in duong_dan.split('.'):
        if obj is None:
            return None
        obj = getattr(obj, p)
    return obj() if callable(obj) else obj


class Crud:
    def __init__(self, bp, ten, url, model, tieu_de, truong, cot, cot_ma, chuc_nang, tim_kiem=(),
                 sap_xep=None, mac_dinh=None, sau_luu=None, hanh_dong=(), bieu_tuong='bi-list', loc=None):
        self.bp, self.ten, self.url, self.model, self.tieu_de = bp, ten, url, model, tieu_de
        self.truong, self.cot, self.cot_ma, self.chuc_nang = truong, cot, cot_ma, chuc_nang
        self.tim_kiem = tim_kiem
        self.sap_xep = sap_xep if sap_xep is not None else getattr(model, cot_ma)
        self.mac_dinh, self.sau_luu, self.hanh_dong = mac_dinh, sau_luu, hanh_dong
        self.bieu_tuong, self.loc = bieu_tuong, loc
        self._dang_ky()

    # ------------------------------------------------------------------ routes
    def ep(self, hanh_dong):
        return f'{self.bp.name}.{self.ten}_{hanh_dong}'

    def _dang_ky(self):
        cn = self.chuc_nang
        r = self.bp.add_url_rule
        r(f'/{self.url}', f'{self.ten}_list', quyen_required(cn, 'xem')(self.danh_sach))
        r(f'/{self.url}/them', f'{self.ten}_them', quyen_required(cn, 'them')(self.them), methods=['GET', 'POST'])
        r(f'/{self.url}/<int:id>/sua', f'{self.ten}_sua', quyen_required(cn, 'sua')(self.sua),
          methods=['GET', 'POST'])
        r(f'/{self.url}/<int:id>/xoa', f'{self.ten}_xoa', quyen_required(cn, 'xoa')(self.xoa), methods=['POST'])
        r(f'/{self.url}/xuat-excel', f'{self.ten}_xuat', quyen_required(cn, 'in_an')(self.xuat_excel))
        r(f'/{self.url}/mau-excel', f'{self.ten}_mau', quyen_required(cn, 'them')(self.mau_excel))
        r(f'/{self.url}/nhap-excel', f'{self.ten}_nhap', quyen_required(cn, 'them')(self.nhap_excel),
          methods=['POST'])

    def _truy_van(self):
        q = self.model.query
        tu_khoa = request.args.get('q', '').strip()
        if tu_khoa and self.tim_kiem:
            q = q.filter(db.or_(*[getattr(self.model, c).ilike(f'%{tu_khoa}%') for c in self.tim_kiem]))
        if self.loc:
            q = self.loc(q, request.args)
        return q.order_by(self.sap_xep)

    def danh_sach(self):
        trang = self._truy_van().paginate(page=request.args.get('page', 1, type=int), per_page=20,
                            error_out=False)
        return render_template('crud/list.html', v=self, trang=trang, lay=lay_thuoc_tinh)

    def them(self):
        obj = self.model()
        if request.method == 'POST':
            loi = self._gan(obj, lambda t: request.form.get(t.ten), tu_form=True)
            if not loi:
                if self.mac_dinh:
                    self.mac_dinh(obj)
                db.session.add(obj)
                return self._luu(obj, moi=True)
            for e in loi:
                flash(e, 'danger')
        return render_template('crud/form.html', v=self, obj=obj, du_lieu=request.form)

    def sua(self, id):
        obj = db.session.get(self.model, id) or abort(404)
        if request.method == 'POST':
            loi = self._gan(obj, lambda t: request.form.get(t.ten), tu_form=True)
            if not loi:
                return self._luu(obj, moi=False)
            db.session.rollback()
            for e in loi:
                flash(e, 'danger')
        return render_template('crud/form.html', v=self, obj=obj, du_lieu=request.form)

    def _luu(self, obj, moi):
        try:
            if self.sau_luu:
                self.sau_luu(obj, moi)
            db.session.commit()
        except LoiNghiepVu as e:
            db.session.rollback()
            flash(str(e), 'danger')
            return render_template('crud/form.html', v=self, obj=obj, du_lieu=request.form)
        flash(f'Đã {"thêm" if moi else "cập nhật"} {self.tieu_de.lower()}: {obj}', 'success')
        return redirect(request.args.get('next') or url_for(self.ep('list')))

    def xoa(self, id):
        obj = db.session.get(self.model, id) or abort(404)
        ten = str(obj)
        lien_quan = self._lien_quan(obj)
        if not lien_quan:
            try:
                db.session.delete(obj)
                db.session.commit()
                flash(f'Đã xóa {ten}.', 'success')
                return redirect(url_for(self.ep('list')))
            except IntegrityError:
                db.session.rollback()
                obj = db.session.get(self.model, id)
        if hasattr(obj, 'trang_thai'):
            obj.trang_thai = False
            db.session.commit()
            flash(f'{ten} đã phát sinh dữ liệu liên quan nên được chuyển sang "Ngừng sử dụng" thay vì xóa.',
                  'warning')
        else:
            flash(f'Không thể xóa {ten} vì đã có dữ liệu liên quan.', 'danger')
        return redirect(url_for(self.ep('list')))

    @staticmethod
    def _lien_quan(obj):
        for rel in inspect(type(obj)).relationships:
            if rel.direction.name == 'ONETOMANY' and 'delete' not in rel.cascade and getattr(obj, rel.key):
                return rel.key
        return None

    # ------------------------------------------------------------------ gan du lieu
    def _gan(self, obj, lay, tu_form=False):
        with db.session.no_autoflush:
            return self._gan_du_lieu(obj, lay, tu_form)

    def _gan_du_lieu(self, obj, lay, tu_form):
        loi = []
        for t in self.truong:
            if not tu_form and not t.excel:
                continue
            gt = lay(t)
            if isinstance(gt, str):
                gt = gt.strip()
            if t.kieu == 'bool':
                if tu_form:
                    setattr(obj, t.ten, gt in ('1', 'on', 'true'))
                elif gt not in (None, ''):
                    setattr(obj, t.ten, str(gt).strip().lower() in ('1', 'x', 'có', 'co', 'true', 'yes'))
                continue
            if t.kieu == 'password':
                if gt:
                    if len(gt) < 6:
                        loi.append(f'{t.nhan}: tối thiểu 6 ký tự.')
                    else:
                        obj.set_password(gt)
                continue
            if gt in (None, ''):
                if t.bat_buoc:
                    loi.append(f'Vui lòng nhập "{t.nhan}".')
                else:
                    setattr(obj, t.ten, None if t.kieu != 'number' else (0 if t.min is not None else None))
                continue
            if t.kieu == 'number':
                v = so_thuc(gt, None)
                if v is None or (t.min is not None and v < t.min):
                    loi.append(f'"{t.nhan}" phải là số' + (f' ≥ {t.min:g}.' if t.min is not None else '.'))
                    continue
                cot = self.model.__table__.columns.get(t.ten)
                setattr(obj, t.ten, int(v) if cot is not None and isinstance(cot.type, db.Integer) else v)
            elif t.kieu == 'date':
                v = doc_ngay(gt)
                if v is None:
                    loi.append(f'"{t.nhan}" không đúng định dạng ngày.')
                    continue
                setattr(obj, t.ten, v)
            elif t.kieu == 'select' and t.model is not None:
                if tu_form:
                    ref = db.session.get(t.model, int(gt)) if str(gt).isdigit() else None
                else:
                    ref = t.model.query.filter(getattr(t.model, t.cot_ma) == str(gt)).first()
                if ref is None:
                    loi.append(f'"{t.nhan}" không hợp lệ: {gt}.')
                    continue
                setattr(obj, t.ten, ref.id)
            elif t.kieu == 'select' and t.chon:
                if str(gt) not in t.chon:
                    loi.append(f'"{t.nhan}" không hợp lệ: {gt}.')
                    continue
                setattr(obj, t.ten, str(gt))
            else:
                setattr(obj, t.ten, str(gt) if not isinstance(gt, float) or not gt.is_integer() else str(int(gt)))
        # kiem tra trung ma / cot duy nhat
        for t in self.truong:
            col = getattr(self.model, t.ten, None)
            if col is None or t.kieu in ('password', 'bool'):
                continue
            cot = self.model.__table__.columns.get(t.ten)
            if cot is not None and cot.unique:
                gt = getattr(obj, t.ten)
                if gt not in (None, ''):
                    trung = self.model.query.filter(col == gt, self.model.id != (obj.id or 0)).first()
                    if trung:
                        loi.append(f'{t.nhan} "{gt}" đã tồn tại.')
        return loi

    def gia_tri_form(self, obj, t, du_lieu):
        if du_lieu and t.ten in du_lieu:
            return du_lieu.get(t.ten)
        gt = getattr(obj, t.ten, None)
        if t.kieu == 'password':
            return ''
        if t.kieu == 'date' and isinstance(gt, date):
            return gt.isoformat()
        if t.kieu == 'number' and isinstance(gt, float) and gt.is_integer():
            return int(gt)
        return '' if gt is None else gt

    # ------------------------------------------------------------------ excel
    def _cot_excel(self):
        return [t for t in self.truong if t.excel and t.kieu != 'password']

    def _gia_tri_excel(self, obj, t):
        gt = getattr(obj, t.ten)
        if t.kieu == 'select' and t.model is not None:
            ref = db.session.get(t.model, gt) if gt else None
            return getattr(ref, t.cot_ma) if ref else None
        return gt

    def xuat_excel(self):
        cot = self._cot_excel()
        dong = [[self._gia_tri_excel(o, t) for t in cot] for o in self._truy_van()]
        return excel.xuat(f'{self.ten}_{date.today():%Y%m%d}.xlsx', f'DANH SÁCH {self.tieu_de.upper()}',
                          [t.nhan_excel for t in cot], dong)

    def mau_excel(self):
        return excel.mau_nhap(f'mau_nhap_{self.ten}.xlsx', [t.nhan_excel for t in self._cot_excel()])

    def nhap_excel(self):
        cot = self._cot_excel()
        try:
            dong = excel.doc(request.files.get('file'), [t.nhan_excel for t in cot])
        except LoiNghiepVu as e:
            flash(str(e), 'danger')
            return redirect(url_for(self.ep('list')))
        cot_ma = next(t for t in cot if t.ten == self.cot_ma)
        tat_ca_loi, them, sua = [], 0, 0
        for i, row in enumerate(dong, start=2):
            ma = row.get(cot_ma.nhan)
            ma = str(int(ma)) if isinstance(ma, float) and ma.is_integer() else (str(ma).strip() if ma else '')
            obj = self.model.query.filter(getattr(self.model, self.cot_ma) == ma).first() if ma else None
            moi = obj is None
            if moi:
                obj = self.model()
                db.session.add(obj)
            loi = self._gan(obj, lambda t: row.get(t.nhan), tu_form=False)
            if moi and self.mac_dinh:
                self.mac_dinh(obj)
            if loi:
                tat_ca_loi += [f'Dòng {i}: {e}' for e in loi]
                continue
            try:
                if self.sau_luu:
                    self.sau_luu(obj, moi)
                db.session.flush()
            except (LoiNghiepVu, IntegrityError) as e:
                tat_ca_loi.append(f'Dòng {i}: {e}')
                break
            them, sua = them + moi, sua + (not moi)
        if tat_ca_loi:
            db.session.rollback()
            flash('Nhập Excel thất bại, không có dòng nào được lưu. ' + ' | '.join(tat_ca_loi[:8]), 'danger')
        else:
            db.session.commit()
            flash(f'Nhập Excel thành công: thêm mới {them}, cập nhật {sua} dòng.', 'success')
        return redirect(url_for(self.ep('list')))

    @property
    def co_quyen(self):
        return {q: current_user.co_quyen(self.chuc_nang, q) for q in ('them', 'sua', 'xoa', 'in_an')}
