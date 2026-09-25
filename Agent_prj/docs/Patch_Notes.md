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

## [CHECKPOINT] - Nghiệm thu Tầng Backend (Model & ViewModel) - Kết thúc Phiên 1
**Trạng thái hệ thống hiện tại (ĐÃ HOÀN THIỆN):**
- **Model:** TcpServerModel xử lý kết nối, DataParserModel bóc tách CSV thành Dict.
- **ViewModel:** 
  - LineViewModel: Quản lý trạng thái từng máy (OK, NG, Status). Đã sửa lỗi biến và chuẩn hóa OOP.
  - DashboardViewModel: Định tuyến data động theo machine_id. Hàm calculate_summary đếm tổng số máy, số máy RUNNING/OFFLINE và gán mock-data (Machine OK) chuẩn xác.
- Đã test thành công việc đấu dây ngầm (Wiring) trong main.py. Mất mạng/Có mạng tự động trigger tính toán lại toàn bộ.

**Nhiệm vụ cho Phiên làm việc tiếp theo (Tầng View - UI):**
- [x] Sử dụng Qt Designer thiết kế 2 file: main_window.ui (Khung chính + Summary) và line_card.ui (Template thẻ máy).
- [x] Sử dụng cơ chế load động Template: Đọc file line_card.ui N lần dựa trên số lượng máy trong cấu hình và nhét vào ScrollArea.
- [x] Thực hiện Binding (Nối dây UI): Cắm Signal từ ViewModel vào các phần tử giao diện.

## [CHECKPOINT] - Giai đoạn 4: Triển khai Tầng View (UI) Động 
**Trạng thái hệ thống hiện tại:**
- Đã cung cấp scaffolding cho `views/main_window.ui` và `views/line_card.ui`.
- Đã viết class `views/main_window.py` có khả năng tự động load `.ui` template và nhồi vào lưới Grid Layout của Scroll Area.
- Cập nhật lại `main.py` để khởi tạo View và truyền `DashboardViewModel` vào nhằm thực hiện cơ chế nối dây Signals (Binding) chuẩn MVVM.

**Hướng dẫn phát triển tiếp:**
- User mở Qt Designer chỉnh sửa thẩm mỹ cho 2 file UI (không đổi tên ObjectName để giữ Binding).
- Bắt đầu chạy test thử từ file `main.py`.


## [v0.2.0] - Giai đoạn 2: Tích hợp TCP Client & Tính toán OEE
### Thêm mới (Added)
- Tích hợp thành công luồng TCP Client (Port 30005) thông qua TcpClientManager quản lý mảng Object đa luồng.
- Cơ chế Máy trạng thái (State Machine) OEE: Chuyển quyền quyết định trạng thái (RUNNING, IDLE, LOSS, ERROR) vào LineViewModel thông qua hàm evaluate_status().
- Tích hợp QTimer nhịp 1 giây (	ick_1_second) để tự động cộng dồn thời gian Ca Ngày / Ca Đêm dựa vào giờ hệ thống.

### Thay đổi (Changed)
- **Fix TCP Fragmentation:** Xử lý triệt để lỗi thiếu/ghép gói tin TCP bằng cơ chế uffer += chunk. Đảm bảo độ mượt mà khi unpack chuẩn 1440 bytes.
- **Fix Signal Dropping:** Áp dụng unctools.partial thay cho lambda để khắc phục lỗi mất tín hiệu (băng qua Thread) từ TCP Client lên Main UI.
- Tối giản hóa Giao diện Thẻ máy (ẩn bộ đếm 
un_time).

### Kế hoạch (Planned)
- Bổ sung và tinh chỉnh giao diện cho các thẻ (Line Card) để hiển thị trực quan thông số OEE Ca Ngày / Ca Đêm.
- Căn chỉnh Layout, GroupBox và CSS (màu sắc/bố cục) để giao diện thẻ nhìn hiện đại.
- Test tổng thể luồng UI Card khi có nhiều máy chạy song song.

## [v0.3.0] - Bổ sung Dashboard con (Sub-Dashboard) cho từng máy
### Thêm mới (Added)
- Tạo mới file views/machine_dashboard.ui (giao diện Sub-Dashboard với 3 vùng: Sản lượng, Downtime ca, Bảng lịch sử cảnh báo).
- Tạo class MachineDashboardDialog (trong views/machine_dashboard_dialog.py) kế thừa QDialog để hiển thị popup. Quản lý việc tự động kết nối và ngắt kết nối tín hiệu (signal_update_ui) để tránh memory leak.
- Thêm cơ chế bắt sự kiện click trên thẻ máy (Event Filter) thông qua installEventFilter trong main_window.py (chỉ bắt ở thẻ cha card_widget, để sự kiện tự động sủi bọt từ các widget con theo chuẩn thiết kế Qt).
- Bổ sung logic ghi nhận lịch sử trạng thái (ERROR, LOSS, IDLE) vào self.error_history bên trong line_vm.py, lưu trữ kèm cả chuỗi thông báo nguyên bản.

### Thay đổi (Changed)
- Cập nhật cấu trúc từ điển (dict) của error_history trong line_vm.py: đổi key "error" thành "message" và thêm key "status" để đồng bộ hóa với code hiển thị UI.

### Kế hoạch (Planned)
- Triển khai tính năng tổng hợp lịch sử lỗi (Bảng tóm tắt lỗi của tất cả các máy) nằm ở góc dưới bên phải của màn hình Dashboard tổng.

## [v0.3.1] - Bảng tổng hợp lỗi toàn nhà máy (Global Alarms)
### Thêm mới (Added)
- Phân tích và tạo file iews/global_alarms.ui: Popup chuẩn mực hiển thị 7 cột dữ liệu cảnh báo từ toàn bộ các máy trong nhà máy.
- Tạo class GlobalAlarmsDialog (trong iews/global_alarms_dialog.py):
  - Tự động vòng lặp qua tất cả các máy trong config (không bị ảnh hưởng bởi tab đang mở).
  - Gom nhóm (aggregate) các lỗi để đếm số lần (Count), cập nhật thời gian phát sinh gần nhất và thời gian xử lý gần nhất.
  - Phân loại trạng thái Active (Đỏ) và Resolved (Xanh lá).
  - Tự động bắt sự kiện signal_summary_updated để cập nhật bảng Realtime.
  - Tích hợp 2 ComboBox hỗ trợ lọc theo Tên Máy và Trạng Thái (Active/Resolved).
- Tích hợp với giao diện chính: Khôi phục layout thẻ máy và gắn sự kiện click vào nút tn_alarm_total trên Main Window để mở Popup.

## [v0.3.2] - Giai đoạn 5: Tối ưu hóa & Bảo mật & Build
### Cập nhật & Fix bug (Updated & Fixed)
- **Production_vm.py**: Sửa lỗi TypeError do phát signal sai kiểu dict (đổi {} thành []). Xóa bỏ các ký tự tiếng Việt trong print để tránh UnicodeEncodeError khi chạy PyInstaller --noconsole.
- **main_window.py**: Sửa lỗi sập UI khi bảng không khớp số lượng máy bằng cách tạo 
ow_map và khởi tạo QTableWidgetItem linh hoạt. Khắc phục lỗi label lbl_machine_id bị Qt Designer cắt chữ bằng cách ép resize chiều rộng lên 250px bằng Python.
- **dashboard_vm.py**: Nâng cấp bộ đếm giờ của tính năng Báo cáo Teams. Chuyển từ QTimer chạy ngầm tùy ý sang logic bắn tự động chính xác vào đúng phút 00 của các khung giờ chẵn (VD: 14:00, 16:00), đảm bảo tính nhất quán của dữ liệu sản xuất.
- **Team_publisher.py**: 
  - Tách URL Webhook của Microsoft Teams ra khỏi mã nguồn, lưu vào thư mục security/secrets.json để tránh lộ lọt trên GitHub (Giải quyết cảnh báo GitGuardian).
  - Tích hợp hàm đọc đường dẫn động hỗ trợ cả môi trường VS Code (__file__) và môi trường đóng gói PyInstaller (sys._MEIPASS / sys.executable).
  - Thêm erify=False vào 
equests.post để vượt qua bộ lọc SSL Inspection (HTTP 403 Forbidden / SSLCertVerificationError) của Tường lửa Fortinet công ty.
- **data_logger.py**: Bổ sung getattr(sys, 'frozen', False) để đảm bảo thư mục LOG được ghi trực tiếp vào ổ cứng cạnh file .exe, thay vì ghi nhầm vào ổ Temp _MEIPASS của PyInstaller rồi bị xóa mất.

### Kế hoạch (Planned)
- Hướng dẫn người dùng sử dụng RustDesk hoặc AnyDesk để truy cập từ xa vào Mini PC Windows 7 trên xưởng mà không cần cài đặt VPN hay tài khoản phức tạp.
- Đóng gói toàn bộ cấu hình vào main.exe bằng --add-data nếu có nhu cầu tạo Single Executable.
