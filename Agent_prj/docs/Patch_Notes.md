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
- **Dynamic Scaling (Mở rộng động)**: Đặc biệt lưu ý, số lượng dây chuyền không đóng cứng (hardcode) là 12. Hệ thống phải hỗ trợ **x máy**. Số lượng máy được quyết định bằng cấu hình (Config). Cả UI Component (LineCardWidget) và ViewModel (LineViewModel) sẽ được khởi tạo linh hoạt bằng vòng lặp dựa trên biến `x` này.
