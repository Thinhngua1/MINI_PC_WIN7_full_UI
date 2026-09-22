import json
import os
import requests
import threading
import time
from datetime import datetime
from typing import Optional, Dict
from models.data_logger import DataLoggerModel
from models.api_publisher import ApiPublisherModel
from PyQt5.QtCore  import QObject, pyqtSignal

class DataParserModel(QObject):
    # luồng RB làm client
    signal_log_of_dataParser = pyqtSignal(str)
    # luồng RB làm server
    signal_client_data = pyqtSignal(dict) 

    def __init__(self):
        super().__init__()# kế thừa cho signal
        # Đọc file config một lần duy nhất lúc khởi động app
        try:
            #lay path config file
            this_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(this_dir)   
            config_path = os.path.join(parent_dir,"config", "config.json")

            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            print("Lỗi đọc file config SQL:", e)
            self.config = {}


        # Khóa an toàn khi có nhiều luồng (thread) cùng gọi hàm print
        self.lock = threading.Lock()

        self.logger = DataLoggerModel() # tạo instance cho DataLoggerModel
        self.publisher = ApiPublisherModel() #tạo instance cho ApiPublisherModel


    def parse_csv(self, raw_data) -> Optional[Dict[str, str]]:
        try: 
            # Ví dụ raw_data = "DRB_02,A175,1000,900,100,90,1,Change tray,"
            # 1. Quét qua các cấu hình máy để tìm xem chuỗi này của máy nào
            for _, val in self.config["parser_rules"].items():
                keyword = val.get("keyword")
                
                # Nếu tìm thấy từ khóa trong chuỗi
                if raw_data.startswith(keyword):
                    #bổ sung ngày h
                    day = datetime.now().strftime("%Y-%m-%d")
                    hour = datetime.now().strftime("%H:%M:%S")

                    # Cắt chuỗi và loại bỏ khoảng trắng dư thừa
                    parts = [p.strip() for p in raw_data.split(",")]    
                    
                    # 2. Ráp dữ liệu dựa theo "mapping" trong config
                    extracted_data = {}
                    mapping = val.get("mapping")
                    
                    for index_str, field_name in mapping.items():
                        idx = int(index_str) # Chuyển "0", "1" thành số nguyên
                        if idx < len(parts):
                            extracted_data[field_name] = parts[idx]
                        else: 
                            extracted_data[field_name] = ""

                    # 3. Bổ sung các trường hệ thống tự sinh (Không phụ thuộc vào index của chuỗi CSV)
                    extracted_data["date"] = day
                    extracted_data["time"] = f"{day} {hour}"
                    
                    print(f"extracted_data: {extracted_data}")
                    # emit lên UI
                    self.signal_log_of_dataParser.emit(f"extracted_data:{extracted_data}") 
                    # in log
                    self.logger.save_to_local_log(extracted_data)
                    #send to SQL
                    self.publisher._send_to_api(extracted_data)
                    

                    return extracted_data # Gọi 1 lần duy nhất và trả về kết quả
                    {'machine': 'DRB_02', 'model': 'A175', 'total': '1000', 'qtyOk': '650',
                      'qtyNg': '350', 'rate': '65', 'shifts': '1', 'date': '2025-12-12', 'time': '2025-12-12 09:09:10',"type": "Change Tray/Function", 'message':'wait_material'}
            print(f"Chuỗi không chứa từ khóa hợp lệ")    
            return None  # Chuỗi không chứa từ khóa hợp lệ
            
        except Exception as e:
            print(f"[DataParser] Lỗi phân tích dữ liệu: {e}")
            return None 

    def parse_TCP_client (self, raw_data_TCP_client):
        # test data from TCP_client manager
        # print(f"[RADAR PARSER] Đã nhận dict từ Manager: {raw_data_TCP_client}") 
        # 1. Nhận data_dict từ TCP Client Manager
        # {{"machine_id": "DRB_01","robot_mode":7, "ErrorStatus":0}, .....}
        clean_data = raw_data_TCP_client
        # 2. Xử lý( ko làm gì, đảm bảo MVVM)
        
        # 3.  bắn Signal
        self.signal_client_data.emit(clean_data)

if __name__ == "__main__":
    # Import các module cần thiết để test
    import json
    import time
    import os  
    from tcp_server import TcpServerModel
    
    # 1. Tự động dò đường dẫn tới file config.json
    current_dir = os.path.dirname(os.path.abspath(__file__)) # Lấy vị trí file data_parser.py
    config_path = os.path.join(current_dir, "..", "config", "config.json")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # Khởi tạo Parser với bộ luật đọc từ config
    parser = DataParserModel()
    
    # 2. Khởi tạo TCP Server để lấy data sống (live data)
    server = TcpServerModel(8500)
    
    # 3. Tạo một hàm mồi (Dummy function) để hứng tín hiệu từ TCP và vứt vào Parser
    def test_catch_data(client_id, raw_string):
        print(f"\n[TEST] TCP vừa nhận chuỗi từ {client_id}: {raw_string}")
        
        # Gọi parser dịch chuỗi
        clean_dict = parser.parse_csv(raw_string)
        
        if clean_dict:
            print(f"[TEST] Parser bóc tách thành công! Kết quả:")
            print(clean_dict)
        else:
            print("[TEST] Parser thất bại: Chuỗi không hợp lệ hoặc không khớp Config.")

    # 4. Nối dây tín hiệu TCP vào hàm mồi
    server.signal_data_received.connect(test_catch_data)
    
    # 5. Khởi chạy Server
    server.start()
    print("Đang chạy chế độ TEST Parser. Hãy dùng phần mềm gửi 1 chuỗi giả lập qua port 8500...")
    
    # Giữ cho chương trình không bị tắt
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("Đã tắt TEST.")
