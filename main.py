import sys
import json
from PyQt5.QtWidgets import QApplication

# 1. Import các lớp Models
from models.tcp_server import TcpServerModel

# 2. Import các lớp ViewModels
from viewmodels.dashboard_vm import DashboardViewModel

# 3. Import các lớp Views
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # --- KHỞI TẠO CẤU HÌNH ---
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file config/config.json. Vui lòng kiểm tra lại.")
        sys.exit(1)

    # --- KHỞI TẠO TẦNG VIEWMODEL ---
    # Truyền danh sách máy (machines) từ config vào DashboardViewModel
    dashboard_vm = DashboardViewModel(config['machines'])
    
    # --- KHỞI TẠO TẦNG MODEL ---
    # Khởi tạo TCP Server để nhận dữ liệu từ các máy trạm
    tcp_port = config.get('network', {}).get('tcp_listen_port', 8500)
    tcp_server = TcpServerModel(tcp_port)
    
    # --- WIRING (ĐẤU NỐI TÍN HIỆU NGẦM) ---
    # Model (TCP Server) -> ViewModel (Dashboard)
    tcp_server.signal_data_received.connect(dashboard_vm.handle_raw_data)
    tcp_server.signal_connection_changed.connect(dashboard_vm.handle_connection_changed)
    
    # --- KHỞI TẠO TẦNG VIEW ---
    # Khởi tạo Giao diện chính và truyền ViewModel vào để nó tự bind dữ liệu
    main_window = MainWindow(dashboard_vm)
    main_window.show()
    
    # Bắt đầu Server TCP chạy ngầm
    tcp_server.start()
    print(f"Hệ thống đã sẵn sàng lắng nghe ở cổng {tcp_port}!")
    
    # Chạy vòng lặp UI
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
