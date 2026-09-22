import json
import os
import threading
import functools
from PyQt5.QtCore import QObject, pyqtSignal
from models.tcp_client import TCPclientModel

class TcpClientManager(QObject):
    # Tín hiệu gom chung của TẤT CẢ các máy, chuẩn bị bắn sang DataParser
    signal_manager_rcv = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.clients = {}  # Lưu trữ danh sách x Object TCP Client
        # {{"machine_id": "DRB_01","robot_mode":7, "ErrorStatus":0}, .....}
    def start_all_clients(self):
        """Hàm này sẽ được gọi từ main.py lúc khởi động App"""
        # 1. Đọc danh sách Robot từ Config
        robot_list = self.load_config()
        
        # 2. Vòng lặp đẻ ra x Object Client
        for robot in robot_list:
            ip = robot.get("ip")
            port = int(robot.get("port", 30005))
            machine_id = robot.get("machine_id")
            
            # Khởi tạo Object Client 
            client_obj = TCPclientModel(ip, port)
            
            # 3. Gom dây tín hiệu của máy này vào trạm quản lý client
            # Dùng thủ thuật m_id=machine_id để tránh bị đè biến trong vòng lặp for
            client_obj.signal_rcv_by_server.connect(
                # lambda data_dict, m_id=machine_id: self.on_client_receive(m_id, data_dict)
                functools.partial(self.on_client_receive, machine_id)
            )
            
            # Lưu vào danh sách để quản lý (sau này cần ngắt kết nối thì gọi ra)
            self.clients[machine_id] = client_obj
            
            # 4. Kích hoạt Client chạy 
            threading.Thread(target=client_obj.void_server, daemon=True).start()
            
    def load_config(self):
        # Tự động dò đường dẫn tới file config.json
        try:
            #lay path config file
            this_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(this_dir)   
            config_path = os.path.join(parent_dir,"config", "config.json")

            with open(config_path, "r", encoding="utf-8") as f:
                self.config_file_path= json.load(f)
        except Exception as e:
            print("Lỗi đọc file config:", e)
            self.config = {}

        machines = self.config_file_path.get("machines", [])
        servers = self.config_file_path.get("server", [])

        robot_list = []

        for machine, server in zip(machines, servers):
            robot_list.append({
                "machine_id": machine.get("id"),
                "ip": server.get("ip"),
                "port": int(server.get("port", 30005)),
            })

        return robot_list

        # Trả về mẫu: [{"machine_id": "DRB_01", "ip": "192.168.1.10", "port": 5000}, ...]
        
    def on_client_receive(self, machine_id, data_dict):
        print(f"[RADAR MANAGER] Đã nhận dict từ luồng 2: {data_dict} của máy {machine_id}") # Test data từ TCP_client
        """Hàm này tự động nảy số khi BẤT KỲ máy nào gửi data về"""
        # Nhét thêm ID của máy vào data để DataParser biết cục data này của thằng nào
        data_dict["machine_id"] = machine_id
        
        # Bắn sang DataParser
        self.signal_manager_rcv.emit(data_dict) 