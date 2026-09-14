import sys
import json
from PyQt5.QtWidgets import QApplication

# 1. Import các lớp Models
from models.tcp_server import TcpServerModel
from models.data_parser import DataParserModel
from models.api_publisher import ApiPublisherModel

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
        print("Loi: Khong tim thay file config/config.json. Vui long kiem tra lai.")
        sys.exit(1)

    # --- KHỞI TẠO TẦNG VIEWMODEL ---
    dashboard_vm = DashboardViewModel(config['machines'])
    
    # --- KHỞI TẠO TẦNG MODEL ---
    tcp_port = config.get('network', {}).get('tcp_listen_port', 8500)
    tcp_server = TcpServerModel(tcp_port)

    
    # --- KHỞI TẠO TẦNG VIEW ---
    main_window = MainWindow(dashboard_vm)
    
    # 1.1. Log từ Cổng mạng TCP (Nhận Data thô)
    tcp_server.signal_data_received.connect(
        lambda client, msg: main_window.append_sql_log(f"[TCP] Nhận từ {client}: {msg}")
    )
    
    # 1.2. Log từ Cổng mạng TCP (Báo cắm/rút dây mạng)
    tcp_server.signal_connection_changed.connect(
        lambda client, is_conn: main_window.append_sql_log(
            f"[TCP] Client {client} -> {'ĐÃ KẾT NỐI' if is_conn else 'NGẮT KẾT NỐI'}"
        )
    )

    # Model (TCP Server) -> ViewModel (Dashboard) 
    tcp_server.signal_data_received.connect(dashboard_vm.handle_raw_data)
    tcp_server.signal_connection_changed.connect(dashboard_vm.handle_connection_changed)

    # 2 từ  data_parser trả về
    dashboard_vm.parser.signal_log_of_dataParser.connect(main_window.append_sql_log)
    # 3 từ SQL server trả về
    dashboard_vm.parser.publisher.signal_log_updated.connect(main_window.append_sql_log) 


    main_window.show()
    
    # Bắt đầu Server TCP chạy ngầm
    tcp_server.start()
    print(f"He thong da san sang lang nghe o cong {tcp_port}!")
    
    # Chạy vòng lặp UI
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
