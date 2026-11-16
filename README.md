# eMarket – Hệ thống quản lý chuỗi siêu thị (môi trường dev)

Sản phẩm hiện thực yêu cầu `project_16.md`, bám theo các sơ đồ Use Case (`../eMarket_UseCases/`),
Sequence (`../eMarket_SequenceDiagrams/`), Activity (`../eMarket_ActivityDiagrams/`),
Class Diagram (`../eMarket_ClassDiagrams/`) và ERD (`../eMarket_ERD/`).

## 1. Chạy chương trình

Yêu cầu: Python 3.11+ (đã thử trên 3.14), Windows/Linux/macOS.

```bash
cd eMarket
python -m venv venv                         # đã có sẵn thì bỏ qua
venv\Scripts\pip install -r requirements.txt    # Linux/macOS: venv/bin/pip
venv\Scripts\python run.py
```

Mở trình duyệt tại <http://127.0.0.1:5000>.

- Lần chạy đầu, nếu CSDL trống, `run.py` tự tạo dữ liệu mẫu (mất khoảng 30 giây): 1 năm bán hàng, 2 chi nhánh,
  26 mặt hàng, 13 khách hàng, khoảng 1.850 hóa đơn, phiếu nhập, công nợ và cảnh báo.
- Muốn tạo lại dữ liệu từ đầu: `venv\Scripts\python seed.py --reset`.
- Chạy kiểm thử: `venv\Scripts\python -m unittest discover -s tests -v` (22 test, dùng CSDL trong bộ nhớ, không
  ảnh hưởng dữ liệu thật).

### Tài khoản mẫu

| Trang | Tài khoản | Mật khẩu | Vai trò |
|---|---|---|---|
| Quản trị `/dang-nhap` | `admin` | `admin123` | Quản trị viên (toàn quyền) |
| | `quanly1` | `123456` | Quản lý cửa hàng |
| | `nhanvien1`, `nhanvien2` | `123456` | Nhân viên bán hàng |
| | `kho1` | `123456` | Thủ kho |
| Khách hàng `/khach/dang-nhap` | `0901234567` (VIP, có thẻ) | `123456` | Khách hàng |
| | `0283999888` (Đại lý, có công nợ) | `123456` | Khách hàng |
| | `0911222333` (khách mới, chưa có thẻ) | `123456` | Khách hàng |
| Kiosk `/kiosk/` | không cần đăng nhập | | |

## 2. Đối chiếu yêu cầu – chức năng

| Yêu cầu (project_16.md) | Chức năng trong sản phẩm | Đường dẫn |
|---|---|---|
| **Bán hàng:** đặt hàng, quản lý và theo dõi đơn | Khách đặt online qua giỏ hàng; nhân viên xử lý theo luồng *Chờ xử lý → Đang xử lý → Đang giao → Hoàn thành / Hủy*; lịch sử trạng thái hiển thị dạng timeline cho cả nhân viên và khách | `/khach/`, `/ban-hang/don-hang` |
| | Bán tại quầy (POS): quét mã vạch, chọn khách, dùng điểm, tiền mặt / thẻ / chuyển khoản / ghi nợ, in hóa đơn 80mm | `/ban-hang/pos`, `/ban-hang/hoa-don` |
| Giá bán theo từng khách hàng và mặt hàng | Thứ tự áp giá: giá riêng theo (khách, mặt hàng) → chiết khấu theo loại khách → giá niêm yết | `/ban-hang/gia-ban` |
| **Khách hàng:** lập thẻ thân thiết khi mua ≥ 100.000đ trong 1 lần | Hóa đơn nào đạt ngưỡng thì hệ thống tự lập thẻ ngay và POS thông báo; nhân viên cũng lập được thủ công nếu khách từng đạt ngưỡng | `/khach-hang/the-than-thiet` |
| Lịch sử mua hàng | Trang chi tiết khách hàng (nhân viên) và trang "Đơn của tôi" (khách) | `/khach-hang/<id>`, `/khach/don-hang` |
| Quy đổi giá trị mua thành điểm | 10.000đ = 1 điểm; 1 điểm = 100đ khi thanh toán; có lịch sử cộng/trừ điểm | `/khach/tai-khoan` |
| **Danh mục:** NCC, hàng hóa, loại khách hàng | Thêm/sửa/xóa/tìm kiếm, nhập và xuất Excel cho NCC, loại hàng, hàng hóa, loại KH, kho | `/danh-muc/...` |
| **Công nợ** KH và NCC theo chứng từ | Mỗi hóa đơn ghi nợ hoặc phiếu nhập chưa trả hết tạo 1 chứng từ công nợ có hạn thanh toán; thu hoặc trả từng phần; tổng hợp theo khách và NCC | `/cong-no/`, `/cong-no/tong-hop` |
| Tự động cảnh báo nợ quá hạn, vượt mức | Bộ lập lịch kiểm tra mỗi 5 phút và ngay sau mỗi giao dịch; chuông cảnh báo trên thanh trên cùng; cảnh báo tự đóng khi hết vi phạm | `/he-thong/thong-bao` |
| **Tồn kho:** lượng tồn, đã bán, cảnh báo min/max, theo từng kho | Tồn kho và đã bán theo từng (mặt hàng, kho), ngưỡng min/max chỉnh ngay trên bảng, lọc thiếu/vượt; phiếu nhập nhập tay, quét mã hoặc nhập từ Excel | `/ton-kho/`, `/ton-kho/phieu-nhap` |
| **Web tra cứu (kiosk)** không cần đăng nhập | Màn hình cảm ứng: quét hoặc gõ mã, xem giá, HSD (cảnh báo sắp hết hoặc đã hết hạn), xuất xứ, NCC; tự về màn hình chờ sau 90 giây | `/kiosk/` |
| **Thống kê** theo ngày, tháng, năm, mặt hàng, NCC | Biểu đồ và bảng doanh thu, giá vốn, lợi nhuận, số hóa đơn; in và xuất Excel | `/thong-ke/` |
| **Phân quyền** chi tiết theo chức năng, chứng từ | Ma trận quyền Xem/Thêm/Sửa/Xóa/In-Xuất cho từng chức năng, chứng từ và từng người dùng; có bộ quyền mặc định theo vai trò | `/he-thong/nguoi-dung` |
| Sao lưu hằng ngày | Tự sao lưu lúc 23:00 (bù ngay khi khởi động nếu đã quá 24 giờ), giữ 30 bản; sao lưu thủ công và tải về | `/he-thong/sao-luu` |
| Import/Export Excel | Xuất Excel ở mọi danh sách, báo cáo, hóa đơn, tồn kho, công nợ; nhập Excel cho danh mục và phiếu nhập (có file mẫu) | |
| Đọc và in mã vạch nhiều chuẩn | Máy quét (dạng bàn phím) dùng ở POS, phiếu nhập, kiosk; in tem EAN-13, EAN-8, UPC-A, Code 128, Code 39; tự sinh EAN-13 (đầu 893) | `/danh-muc/hang-hoa/in-ma-vach` |
| Giao diện thân thiện màn hình cảm ứng | Nút lớn, POS dạng lưới chạm, kiosk toàn màn hình, bố cục responsive cho máy tính bảng | |

## 3. Kiến trúc (khớp với lifeline trên sơ đồ Sequence)

```
Giao diện (templates/, static/)  →  Controller (app/routes/*)  →  Service nghiệp vụ (app/services/*)  →  Entity (app/models/*)  →  SQLite
```

| Thư mục | Nội dung |
|---|---|
| `app/models/` | Lớp thực thể: `danhmuc` (NCC, LoaiHangHoa, HangHoa, LoaiKhachHang, Kho), `khachhang` (KhachHang, TheThanhThiet, LichSuDiem), `banhang` (DonHang, ChiTietDonHang, LichSuDonHang, HoaDon, GiaBanTheoKH), `tonkho` (TonKho, PhieuNhap), `congno` (CongNo, ThanhToanCongNo), `nguoidung` (NguoiDung, PhanQuyen), `thongbao` |
| `app/services/` | Nghiệp vụ: `banhang` (áp giá, đặt hàng, xử lý đơn, thanh toán), `khachhang` (lập thẻ, tích và trừ điểm), `tonkho` (nhập hàng, cảnh báo min/max), `congno`, `thongbao`, `thongke`, `excel`, `mavach`, `backup`, `scheduler` |
| `app/routes/` | Controller theo phân hệ; kiểm tra quyền bằng `@quyen_required(chuc_nang, quyen)` |
| `seed.py` | Dữ liệu mẫu, sinh bằng chính các service nghiệp vụ nên tồn kho, công nợ và điểm luôn khớp nhau |
| `tests/` | Kiểm thử tích hợp các luồng chính |

Service không tự commit. Controller commit khi thành công và rollback khi gặp `LoiNghiepVu`, nên mỗi thao tác
nghiệp vụ là một giao dịch trọn vẹn: ví dụ thanh toán thì trừ kho, lập hóa đơn, cộng điểm, lập thẻ và ghi công nợ
cùng lúc hoặc không làm gì cả.

## 4. Cấu hình (`config.py`)

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `NGUONG_THE_THAN_THIET` | 100.000 | Giá trị 1 lần mua để được lập thẻ |
| `SO_TIEN_MOI_DIEM` / `GIA_TRI_MOT_DIEM` | 10.000 / 100 | Quy đổi điểm |
| `HAN_MUC_NO_MAC_DINH` / `SO_NGAY_NO_MAC_DINH` | 5.000.000 / 30 | Hạn mức và thời hạn nợ khi loại KH không quy định |
| `SO_NGAY_NO_NCC` | 30 | Hạn trả nợ NCC mặc định |
| `KIEM_TRA_CANH_BAO_PHUT` | 5 | Chu kỳ kiểm tra cảnh báo |
| `BACKUP_GIO` / `BACKUP_GIU_LAI` | 23 / 30 | Giờ sao lưu hằng ngày và số bản giữ lại |
| `KIOSK_TU_RESET_GIAY` | 90 | Thời gian kiosk tự quay về màn hình chờ |
