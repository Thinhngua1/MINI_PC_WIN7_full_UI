
from PyQt5.QtCore import QObject, pyqtSignal
from viewmodels.line_vm import LineViewModel

#import từ data parser(lớp model)
from models.data_parser import DataParserModel

class DashboardViewModel(QObject):
    signal_summary_updated = pyqtSignal(dict) # Phát tín hiệu tổng OK/NG/OEE

    def __init__(self, machines_config): #machines_config đọc từ file config nhưng gọi từ hàm main(theo MVVM)
        super().__init__()
        self.parser = DataParserModel() # thuộc tính parser data
        # Khởi tạo động danh sách các LineViewModel dựa trên số lượng x máy
        self.lines = {}
        #dict để check OFF line
        self.clients = {}

        for mac in machines_config:
            self.lines[mac['id']] = LineViewModel(mac['id'])

    def handle_raw_data(self, client_id, raw_string):
        # 1. Gọi Parser dịch chuỗi -> Nhận về 1 cái Dict sạch sẽ
        clean_dict = self.parser.parse_csv(raw_string)
        
        # Nếu chuỗi lỗi, parser trả về None thì bỏ qua
        if not clean_dict:
            return 
            
        machine_id = clean_dict.get("machine") # Ví dụ: lấy ra chữ 'DRB_02'

        #1.5 ghi vào dict cái client_id  của client mới nhận 
        self. clients[client_id] = machine_id

        # 2. Vứt data cho đúng ông Trưởng Line
        if machine_id in self.lines:
            # Gọi hàm update_data của LineViewModel và ném cái dict cho nó
            self.lines[machine_id].update_data(clean_dict)
            
        # 3. (Làm sau) Cộng dồn OK/NG của cả xưởng để tính Bảng Tổng


    def handle_connection_changed(self, client_id, is_connected): # đọc từ signal_connection_changed of tcp
        # TODO: Chuyển LineViewModel tương ứng sang OFFLINE
        if not is_connected:
            #Mở sổ tay ra tra xem client_id bị rớt mạng là máy nào
            machine_id = self.clients.get(client_id)
            if machine_id and machine_id in self.lines:
                # Gọi ông Trưởng Line đó, ép biến status thành OFFLINE
                self.lines[machine_id].set_offline()
                
                # Xóa khỏi sổ tay
                del self.clients[client_id]
        pass


# ===================== đã test ok ==========
# nếu nỗi path, dùng python -m viewmodels.dashboard_vm.
if __name__ == "__main__":
    import sys
    import os
    from PyQt5.QtWidgets import QApplication
    import json

    # === MẸO PYTHON ĐỂ TEST ĐỘC LẬP TRONG THƯ MỤC CON ===
    # 1. Ép Python nhận diện thư mục gốc để có thể import được folder 'models'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)
    
    # 2. Đổi môi trường làm việc về gốc để tìm thấy file 'config/config.json'
    os.chdir(project_root)
    # ====================================================
    # 1: Tự import lớp TcpServerModel và DashboardViewModel vào đây
    from models.tcp_server import TcpServerModel
    from models.data_parser import DataParserModel

    app = QApplication(sys.argv)
    
    # 2. Đọc config 
    
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    # 3. Khởi tạo Tổ trưởng (Truyền danh sách máy vào)
    dashboard_vm = DashboardViewModel(config['machines'])
    
    # 4. Khởi tạo TCP Server (Cổng 8500)
    tcp_server = TcpServerModel(config['network']['tcp_listen_port'])
    
    # =========================================================
    # 5. ĐÂY LÀ PHẦN QUAN TRỌNG NHẤT: ĐẤU DÂY TÍN HIỆU (WIRING)
    def print_console_data_received(client_id, message):
        print(f"{client_id} da nhận data: message")

    def print_console_machine_offline(client_id, is_connected):
            print(f"{client_id} đã offline ")
    # Cú pháp: obj_phát.tên_tín_hiệu.connect(obj_nhận.hàm_xử_lý)
    # =========================================================
    
    # A: Nối dây nhận data
    # tcp_server.signal_data_received.connect( ...điền vào đây... )
    
    tcp_server.signal_data_received.connect(dashboard_vm.handle_raw_data)
    #  B: Nối dây báo ngắt kết nối
    # tcp_server.signal_connection_changed.connect( ...điền vào đây... )
    tcp_server.signal_connection_changed.connect(dashboard_vm.handle_connection_changed)
    #in ra console để check
    tcp_server.signal_data_received.connect(print_console_data_received)
    tcp_server.signal_connection_changed.connect(print_console_machine_offline)


    # 6. Bật TCP Server
    tcp_server.start()
    print("Hệ thống đã sẵn sàng!")
    
    sys.exit(app.exec_())