# Patch Notes — Factory Monitor Dashboard

## [v0.1.0] - Giai đoạn 1: Phác thảo và Bàn bạc
### Thêm mới (Added)
- Phân tích yêu cầu `Hybrid Workflow` từ tài liệu `config_Agent.txt`.
- Đề xuất kiến trúc phần mềm theo chuẩn **MVVM (Model - View - ViewModel)**.
- Khởi tạo file sơ đồ kiến trúc tư duy tại `docs/architecture.drawio`.

## [v0.1.1] - Tinh chỉnh kiến trúc
### Thay đổi (Changed)
- **DataParserModel**: Cập nhật sơ đồ tư duy. Thống nhất `DataParserModel` chỉ chịu trách nhiệm bóc tách chuỗi CSV thô thành Data Object chuẩn. 
- Loại bỏ logic mapping (gắn biến hiển thị) khỏi lớp Model. Mọi logic ánh xạ dữ liệu lên vị trí UI (Data Binding) sẽ được giao hoàn toàn cho lớp **ViewModel** xử lý.

## [v0.1.2] - Chốt phương án kỹ thuật thực thi
### Kế hoạch (Planned)
- **Luồng dữ liệu Real-time**: Áp dụng luồng bất đồng bộ (Async) cho SQL. UI cập nhật ngay, SQL gửi ngầm.
- **Kiểm tra Offline**: Áp dụng kiểm tra tín hiệu Heartbeat qua port 30003 của TCP.
- **Quy trình làm UI**: Developer (bạn) sẽ trực tiếp phụ trách load và tích hợp file `.ui` từ Qt Designer.
- **Dynamic Scaling (Mở rộng động)**: Hệ thống phải hỗ trợ **x máy**. Số lượng máy được quyết định bằng cấu hình. Cả UI Component và ViewModel sẽ được khởi tạo linh hoạt bằng vòng lặp dựa trên tham số này.

## [v0.2.0] - Giai đoạn 2: Tạo bộ khung (Scaffolding)
### Thêm mới (Added)
- Khởi tạo cấu trúc dự án: `models/`, `viewmodels/`, `views/`, `config/`.
- `config/app_config.json`: Cấu hình khai báo Port (8500), API (SQL Server), và định nghĩa mảng `machines` (x máy).
- `models/tcp_server.py`: Chứa class (rỗng) mô tả các Interface tín hiệu `signal_data_received`, `signal_machine_offline`.
- `models/data_parser.py` & `api_publisher.py`: Các class xử lý dữ liệu và đẩy HTTP POST.
- `viewmodels/dashboard_vm.py`: File quan trọng chứa vòng lặp tự động nạp `x` cái `LineViewModel` dựa trên cấu hình.
- `views/main_window.py`: Chứa class giao diện rỗng, sẵn sàng để load file `.ui` (`uic.loadUi`).
- `main.py`: File tổng khởi tạo 3 lớp M-V-VM và đấu nối các luồng tín hiệu (Wiring) với nhau.

## [v0.3.0] - Giai đoạn 3: Triển khai Model & Kế hoạch mở rộng
### Cập nhật (Updated)
- **TcpServerModel**: Nâng cấp định danh client thành IP:Port để quản lý đa kết nối.
- **DataParserModel**: Tái sử dụng logic mapping từ dự án cũ (tách biệt khỏi SQL).
- **Cấu hình**: Khởi tạo UI dựa trên tổng số line khai báo cố định trong file config, tránh lỗi "máy hỏng tàng hình".

### Kế hoạch tương lai (Future To-Do)
- **Settings UI (Bảng cài đặt admin)**: Tính năng thay đổi số lượng máy (total_lines) hiện tại gán cố định trong file config để đảm bảo an toàn. Khi hệ thống mở rộng, sẽ thiết kế 1 tab Settings bảo mật bằng mật khẩu trên màn hình. Cho phép Admin nhập số lượng máy mới và lưu ngược về Model (ứng dụng Two-Way Binding).

## [CHECKPOINT] - Điểm lưu trạng thái (Tiếp tục tại nhà)
**Trạng thái hệ thống hiện tại:**
- Kiến trúc đang tuân thủ: MVVM, chia luồng độc lập, gán biến bằng Two-Way Binding.
- Đã test thành công luồng: TCP Server -> Data Parser -> DashboardViewModel.
- Đã nắm được cách Wiring (Đấu dây tín hiệu) chuẩn trong file main.py.

**Nhiệm vụ tiếp theo (Đang làm dở):**
Hoàn thiện hàm calculate_summary(self) trong iewmodels/dashboard_vm.py để tính Tổng toàn nhà máy.
- **Thuật toán cần code:** Lặp qua 12 LineViewModel -> Cộng dồn ok_count, 
g_count -> Tính tỷ lệ OEE -> Đếm máy đang RUNNING -> Đóng gói vào Dict -> Phát tín hiệu signal_summary_updated.
