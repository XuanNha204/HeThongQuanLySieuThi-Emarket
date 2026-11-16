"""Sinh / in ma vach nhieu chuan (EAN-13, EAN-8, UPC-A, Code128, Code39)."""
from io import BytesIO

import barcode
from barcode.writer import SVGWriter

from app.services import LoiNghiepVu

CHUAN_MA_VACH = {
    'ean13': 'EAN-13',
    'ean8': 'EAN-8',
    'upca': 'UPC-A',
    'code128': 'Code 128',
    'code39': 'Code 39',
}
_DO_DAI_SO = {'ean13': (12, 13), 'ean8': (7, 8), 'upca': (11, 12)}


def kiem_tra(ma, chuan):
    if chuan not in CHUAN_MA_VACH:
        raise LoiNghiepVu('Chuẩn mã vạch không được hỗ trợ.')
    if not ma:
        raise LoiNghiepVu('Mã vạch trống.')
    if chuan in _DO_DAI_SO:
        if not ma.isdigit() or len(ma) not in _DO_DAI_SO[chuan]:
            raise LoiNghiepVu(f'Mã {CHUAN_MA_VACH[chuan]} phải gồm {_DO_DAI_SO[chuan][1]} chữ số.')
        if len(ma) == _DO_DAI_SO[chuan][1]:
            lop = barcode.get_barcode_class(chuan)
            if lop(ma[:-1]).get_fullcode() != ma:
                raise LoiNghiepVu(f'Mã {ma} sai số kiểm tra (check digit) của chuẩn {CHUAN_MA_VACH[chuan]}.')
    elif chuan == 'code39' and not all(c.isalnum() or c in '-. $/+%' for c in ma.upper()):
        raise LoiNghiepVu('Code 39 chỉ gồm chữ, số và - . $ / + %.')


def svg(ma, chuan='ean13', ghi_chu=True):
    kiem_tra(ma, chuan)
    lop = barcode.get_barcode_class(chuan)
    du_lieu = ma[:-1] if chuan in _DO_DAI_SO and len(ma) == _DO_DAI_SO[chuan][1] else ma
    kwargs = {'add_checksum': False} if chuan == 'code39' else {}
    obj = lop(du_lieu.upper() if chuan == 'code39' else du_lieu, writer=SVGWriter(), **kwargs)
    buf = BytesIO()
    obj.write(buf, options={'module_height': 12, 'font_size': 8, 'text_distance': 4,
                            'quiet_zone': 2, 'write_text': ghi_chu})
    return buf.getvalue()


def sinh_ean13(so):
    """Sinh ma EAN-13 noi bo: tien to 893 (Viet Nam) + 9 so + check digit."""
    goc = f'893{int(so):09d}'
    return barcode.get_barcode_class('ean13')(goc).get_fullcode()
