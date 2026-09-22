from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime # Nhớ import cái này ở đầu file nếu chưa có

class LineViewModel(QObject):
    # Tín hiệu thông báo cho View biết data đã thay đổi để vẽ lại UI
    signal_update_ui = pyqtSignal()

    def __init__(self, machine_id, machine_model):
        super().__init__()
        self.machine_id = machine_id # VD: DRB_02
        self.machine_model =  machine_model #VD: A175
        self.total_count = 0
        self.ok_count = 0
        self.ng_count = 0
        self.rate = 0.0
        self.status = "OFFLINE"
        self.type = ""  # <--- Bổ sung dòng này để lúc mới bật App lên nó rỗng

         # Các thông số từ 2 luồng( tính OEE)
        self.message = ""       # là runMode từ luồng TCP Server

        #  PHẢI KHAI BÁO MẶC ĐỊNH ĐỂ KHÔNG BỊ LỖI KHI LUỒNG 1(TCP server) CHẠY TRƯỚC
        self.error_status = 0
        self.robot_mode = -1
        self.message_ = ""
        self.is_loss_mode = False

        # Cờ chốt trạng thái Loss (Vì nó kéo dài "cho đến khi")
        self.is_loss_mode = False 
        
        # Bộ đếm CA NGÀY
        self.day_idle_time = 0
        self.day_loss_time = 0
        self.day_error_time = 0
        
        # Bộ đếm CA ĐÊM
        self.night_idle_time = 0
        self.night_loss_time = 0
        self.night_error_time = 0

    def update_data(self, parsed_data: dict):
        # Rút số liệu từ Dictionary và gán vào bản thân ông Trưởng Line
        self.machine_model = parsed_data.get("model", "") # A175
        self.total_count = parsed_data.get("total", 0)
        self.ok_count = parsed_data.get("qtyOk", 0)       # 100
        self.ng_count = parsed_data.get("qtyNg", 0)       # 90
        self.rate = parsed_data.get("rate", 0.0)          # 90.0
        # self.status = "RUNNING" # sẽ đọc sau khi team robot chỉnh
        self.message = parsed_data.get("message", "") # Lấy key message từ Dobot
        self.type = parsed_data.get("type", "Change Tray") # nếu dobot ko gửi "type", mặc định Change Tray

        self.evaluate_status()
        # Báo cho View (Giao diện) biết tao vừa có số mới, hãy vẽ lại đi!
        self.signal_update_ui.emit()

    def reset_data(self, parsed_data: dict): # hết ca
        
        self.total_count = parsed_data.get("total", 0)
        self.ok_count = parsed_data.get("qtyOk", 0)       # 100
        self.ng_count = parsed_data.get("qtyNg", 0)       # 90
        self.rate = parsed_data.get("rate", 0.0)          # 90.0
                             
        self.signal_update_ui.emit()

    def set_offline(self):
        self.status = "OFFLINE"
        self.signal_update_ui.emit()

    # luồng 2: Data RB server
    def update_status_from_client(self, clean_dict):
        self.robot_mode = clean_dict.get("robot_mode")
        self.error_status = clean_dict.get("ErrorStatus")

        self.evaluate_status()
            
        #  bắt giao diện LineCard đổi màu chữ/trạng thái (nếu cần)
        self.signal_update_ui.emit()

    def evaluate_status(self):
        self.message_ = str(self.message).strip().lower()

                # === check data từ Dashboard_VM ===
        # print(f"\n[DEBUG] Máy: {self.machine_id} | robot_mode: {self.robot_mode} | error_status: {self.error_status} | message: '{self.message_}'")
        
        if self.robot_mode == 7 and 'pause' in self.message_ :
            self.is_loss_mode = True
        # Kết thúc Loss
        elif self.robot_mode == 7 and 'run' in self.message_:
            self.is_loss_mode = False

        # Dịch mã trạng thái
        if (self.error_status != 0) or (self.robot_mode == 7 and 'error' in self.message_) or (self.robot_mode == 9):
            self.status = "ERROR"
        elif self.is_loss_mode: 
            self.status = "LOSS"
        elif ((self.robot_mode == 7 and 'wait' in self.message_ ) or (not (self.robot_mode == 9 or self.robot_mode == 7))) and (self.status != "ERROR"):
            self.status = "IDLE"
        else:
            self.status = "RUNNING"



    def tick_1_second(self):
 
        # Xem đồng hồ xem đang là Ca Ngày (8h-20h) hay Ca Đêm
        current_hour = datetime.now().hour
        is_day_shift = 8 <= current_hour < 20
        
        # Cộng giây dựa theo ca
        if self.status == "IDLE":
            if is_day_shift: self.day_idle_time += 1
            else: self.night_idle_time += 1
                
        elif self.status == "LOSS":
            if is_day_shift: self.day_loss_time += 1
            else: self.night_loss_time += 1
                
        elif self.status == "ERROR":
            if is_day_shift: self.day_error_time += 1
            else: self.night_error_time += 1
            
        self.signal_update_ui.emit()