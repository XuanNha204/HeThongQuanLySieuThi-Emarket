"""Nhap / xuat du lieu Excel (.xlsx) bang openpyxl."""
from datetime import date, datetime
from io import BytesIO

from flask import send_file
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from app.services import LoiNghiepVu


def xuat(ten_file, tieu_de, tieu_de_cot, dong, tong=None):
    """Tao file Excel gom tieu de, header va cac dong du lieu; tra ve response tai xuong."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Du lieu'
    ws.append([tieu_de])
    ws['A1'].font = Font(bold=True, size=14)
    ws.append([f'Xuất lúc: {datetime.now():%d/%m/%Y %H:%M}'])
    ws.append([])
    ws.append(list(tieu_de_cot))
    for c in ws[4]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='198754')
        c.alignment = Alignment(horizontal='center')
    for r in dong:
        ws.append([_gia_tri(v) for v in r])
    if tong:
        ws.append([_gia_tri(v) for v in tong])
        for c in ws[ws.max_row]:
            c.font = Font(bold=True)
    for i, _ in enumerate(tieu_de_cot, start=1):
        do_rong = max((len(str(ws.cell(row=r, column=i).value or '')) for r in range(4, ws.max_row + 1)), default=10)
        ws.column_dimensions[get_column_letter(i)].width = min(max(do_rong + 2, 10), 60)
    return _gui(wb, ten_file)


def mau_nhap(ten_file, tieu_de_cot, dong_mau=None):
    wb = Workbook()
    ws = wb.active
    ws.append(list(tieu_de_cot))
    for c in ws[1]:
        c.font = Font(bold=True)
    if dong_mau:
        ws.append(list(dong_mau))
    for i, t in enumerate(tieu_de_cot, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(len(t) + 4, 14)
    return _gui(wb, ten_file)


def doc(file_storage, tieu_de_cot):
    """Doc file Excel: dong 1 la header (khop theo nhan cot). Tra ve list dict {nhan_cot: gia_tri}."""
    if not file_storage or not file_storage.filename.lower().endswith('.xlsx'):
        raise LoiNghiepVu('Vui lòng chọn file Excel định dạng .xlsx.')
    try:
        wb = load_workbook(file_storage, data_only=True, read_only=True)
    except Exception:
        raise LoiNghiepVu('Không đọc được file Excel.')
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else '' for h in next(rows, [])]
    thieu = [t for t in tieu_de_cot if t.rstrip(' *') not in [h.rstrip(' *') for h in header]]
    if len(thieu) == len(tieu_de_cot):
        raise LoiNghiepVu('File không đúng mẫu: không tìm thấy cột nào khớp. Hãy tải file mẫu.')
    chi_so = {h.rstrip(' *'): i for i, h in enumerate(header) if h}
    ket_qua = []
    for r in rows:
        if r is None or all(v in (None, '') for v in r):
            continue
        ket_qua.append({t.rstrip(' *'): (r[chi_so[t.rstrip(' *')]] if t.rstrip(' *') in chi_so
                                         and chi_so[t.rstrip(' *')] < len(r) else None)
                        for t in tieu_de_cot})
    return ket_qua


def _gia_tri(v):
    if isinstance(v, bool):
        return 'Có' if v else 'Không'
    if isinstance(v, datetime):
        return v.strftime('%d/%m/%Y %H:%M')
    if isinstance(v, date):
        return v.strftime('%d/%m/%Y')
    return v


def _gui(wb, ten_file):
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=ten_file,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
