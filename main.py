import sys
import json
from PyQt5.QtWidgets import QApplication

# 1. Import các lớp Models
from models.tcp_server import TcpServerModel
from models.data_parser import DataParserModel
from models.api_publisher import ApiPublisherModel

# 2. Import các lớp ViewModels
from viewmodels.dashboard_vm import DashboardViewModel
from viewmodels.Production_vm import ProductionViewModel

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
    production_vm = ProductionViewModel()
    # ===== TEST: Xóa 3 dòng này sau khi verify xong =====
    fake_snapshot = {
        machine_id: {"ok": 99, "ng": 1, "total": 100}
        for machine_id in dashboard_vm.lines.keys()
    }
    production_vm.save_hourly_snapshot("11:00", fake_snapshot)
    # =====================================================


        # --- KHỞI TẠO TẦNG MODEL ---
    tcp_port = config.get('network', {}).get('tcp_listen_port', 8500)
    tcp_server = TcpServerModel(tcp_port)

    
    # --- KHỞI TẠO TẦNG VIEW ---
    main_window = MainWindow(dashboard_vm)

       
    # 1.1. Log từ Cổng mạng TCP (Nhận Data thô) về main
    tcp_server.signal_data_received.connect(
        lambda client, msg: main_window.append_sql_log(f"[TCP] Nhận từ {client}: {msg}")
    )
    
    # 1.2. Log từ Cổng mạng TCP (Báo cắm/rút dây mạng) về main
    tcp_server.signal_connection_changed.connect(
        lambda client, is_conn: main_window.append_sql_log(
            f"[TCP] Client {client} -> {'ĐÃ KẾT NỐI' if is_conn else 'NGẮT KẾT NỐI'}"
        )
    )

    # Model (TCP Server) -> ViewModel (Dashboard) 
    tcp_server.signal_data_received.connect(dashboard_vm.handle_raw_data)
    tcp_server.signal_connection_changed.connect(dashboard_vm.handle_connection_changed)

    # 2 từ  data_parser trả về main
    dashboard_vm.parser.signal_log_of_dataParser.connect(main_window.append_sql_log)
    # 3 từ SQL server trả về main
    dashboard_vm.parser.publisher.signal_log_updated.connect(main_window.append_sql_log) 
    # từ Dashboard từ production 
    dashboard_vm.signal_hourly_data.connect(production_vm.save_hourly_snapshot)
    # từ Dashboard -> time, Shift
    dashboard_vm.signal_time.connect(main_window.update_header_time)

    # View (MainWindow) yêu cầu tải data -> ném cho ProductionVM 
    main_window.signal_request_load_data.connect(production_vm.load_data_by_date)

    production_vm.signal_table_data_ready.connect(main_window.update_production_table)

    main_window.show()
    
    # Bắt đầu Server TCP chạy ngầm
    tcp_server.start()
    print(f"He thong da san sang lang nghe o cong {tcp_port}!")
    
    # Chạy vòng lặp UI
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
