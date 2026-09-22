from PyQt5.QtCore import QObject, pyqtSignal
from viewmodels.line_vm import LineViewModel


from PyQt5.QtCore import Qt,QTimer, QDateTime

#import từ data parser(lớp model)
from models.data_parser import DataParserModel

class DashboardViewModel(QObject):
    signal_summary_updated = pyqtSignal(dict) # Phát tín hiệu (Tổng/OK/NG/wait_material,alarm, running, offline)
    signal_hourly_data = pyqtSignal(str, dict)
    signal_time = pyqtSignal(str, str)

    def __init__(self, machines_config): #machines_config đọc từ file config nhưng gọi từ hàm main(theo MVVM)
        super().__init__()
        self.parser = DataParserModel() # thuộc tính parser data
        # Khởi tạo động danh sách các LineViewModel dựa trên số lượng x máy
        self.lines = {} # có dạng: { 'DRB_02': QObject của LineViewModel}
        # để check OFF line
        self.clients = {}  # dạng: {'192.168.x.x:8500' : 'DRB_02'}

        # khởi tạo instance cho ProductionViewModel
        
        for mac in machines_config:
            self.lines[mac['id']] = LineViewModel(mac['id'], mac['name']) # khởi tạo các máy

        # Bật đồng hồ nghiệp vụ
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.on_timer_tick)
        self.clock_timer.start(1000)

        self.last_minute = -1

    def handle_raw_data(self, client_id, raw_string):
        # 1. Gọi Parser dịch chuỗi -> Nhận về 1 cái Dict sạch sẽ
        clean_dict = self.parser.parse_csv(raw_string)
        
        # Nếu chuỗi lỗi, parser trả về None thì bỏ qua
        if not clean_dict:
            return 
            
        machine_id = clean_dict.get("machine") # Ví dụ: lấy ra name 'DRB_02'

        #1.5 ghi vào dict cái client_id  của client mới nhận 
        if client_id not in self.clients:
            self.clients[client_id] = set() # tạo 1 set rỗng
        self.clients[client_id].add(machine_id) # thêm tên máy nếu ko trùng lặp(IP, tên máy )

        # 2. Vứt data cho đúng ông Trưởng Line(card UI client riêng)
        if machine_id in self.lines:
            # Gọi hàm update_data của LineViewModel và ném cái dict cho nó
            self.lines[machine_id].update_data(clean_dict)
        # update summary 
        self.calculate_summary()
        
    def handle_connection_changed(self, client_id, is_connected): 
        # Chuyển LineViewModel tương ứng sang OFFLINE
        if not is_connected:
            # Lấy ra cái Giỏ chứa các máy dùng chung client_id (hoặc giỏ rỗng nếu không có)
            machine_ids = self.clients.get(client_id, set())
            
            # Duyệt qua từng máy trong giỏ và set OFFLINE
            for machine_id in machine_ids:
                if machine_id in self.lines:
                    self.lines[machine_id].set_offline()
                
            # Xóa giỏ khỏi sổ tay
            if client_id in self.clients:
                del self.clients[client_id]
                
        # update summary  
        self.calculate_summary()

    #luồng data từ RB server
    def update_time_data(self, clean_dict):
        # """Hứng data thời gian (Luồng số 2) từ DataParser bắn sang"""
        machine_id = clean_dict.get("machine_id")
        
        # Nếu máy này có tồn tại trong danh sách quản lý
        if machine_id in self.lines:
            # Vứt cục data trạng thái cho máy đó tự nhai
            self.lines[machine_id].update_status_from_client(clean_dict)

   
    def calculate_summary(self):
        #1. tạo các biến, thêm vào signal_summary_updated sau
        total_machine = len(self.lines) 
        
        machine_running = 0
        machine_offline = 0
        machine_Alarm =  0
        machine_WAITING_Material =  0
                              
        # 2. duyệt qua các line
        for line in self.lines.values():
            if line.status == "OFFLINE":
                machine_offline += 1
            elif line.status == "RUNNING":
                if line.message == 'wait_material':
                    machine_WAITING_Material +=1
                machine_running += 1
                 
        # nhét vào dict
        summary_str = {
            "total_machine":total_machine,
            "machine_Alarm":machine_Alarm,
            "machine_WAITING":machine_WAITING_Material,
            "machine_running": machine_running,
            "machine_offline": machine_offline
        }

        self.signal_summary_updated.emit(summary_str)

    def on_timer_tick(self):
        now = QDateTime.currentDateTime()
        time_str = now.toString("HH:mm:ss dd/MM/yyyy")
        
        # Tính ca làm việc
        h, m, s = now.time().hour(), now.time().minute(), now.time().second()
        shift_str = "1(08:00-20:00)" if 8 <= h < 20 else "2(20:00-08:00)"

        # THÊM ĐOẠN NÀY ĐỂ KÍCH HOẠT ĐỒNG HỒ OEE CỦA TỪNG MÁY
        # Lặp qua tất cả các máy và hô khẩu lệnh: "Cộng 1 giây!"
        for line_vm in self.lines.values():
            line_vm.tick_1_second()

        # 1 phút bắn 1 lần -> snapshot lưu data
        if m != self.last_minute:
            self.last_minute = m

            hour_str = f"{h:02d}:00"
            
            # Tự động gom hết data của 24 máy lại thành 1 Dict
            snapshot_data = {}
            for machine_id, line_vm in self.lines.items():
                snapshot_data[machine_id] = {
                    "ok": line_vm.ok_count,
                    "ng": line_vm.ng_count,
                    "total": line_vm.total_count
                }
            
            # Phát tín hiệu 
            self.signal_hourly_data.emit(hour_str, snapshot_data)
        self.signal_time.emit(time_str,shift_str)

                # ==========================================
        # KÍCH HOẠT ĐỒNG HỒ OEE:
        # ==========================================
        for machine_id, line_vm in self.lines.items():
            if hasattr(line_vm, 'tick_1_second'):
                line_vm.tick_1_second()

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