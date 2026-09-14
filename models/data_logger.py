import os
import json
import threading
from datetime import datetime

class DataLoggerModel:
    def __init__(self):
        # Khởi tạo cái khóa để chống xung đột khi ghi file
        self.lock = threading.Lock()

        # 1. Xác định đường dẫn tuyệt đối đến thư mục LOG (Dùng os.path)
        self.today_str = datetime.now().strftime("%Y-%m-%d")

        self.dir = os.path.dirname(os.path.abspath(__file__))   # .../models
        self.parent_dir = os.path.dirname(self.dir)             # thư mục gốc của project

       
        # 3. Tạo đường dẫn file hoàn chỉnh (nối thư mục LOG và tên file)
        self.log_dir = os.path.join(self.parent_dir, "LOG")    # nối với thư mục LOG

        # Tạo thư mục LOG nếu nó vô tình bị xóa
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        

    def save_to_local_log(self, parsed_data: dict):
        # 2. Tạo tên file theo ngày hiện tại. 
        filename = os.path.join(self.log_dir, f"log_{self.today_str}.json")
       
        # 4. Kiểm tra xem file đã tồn tại chưa (os.path.exists).
        if  os.path.exists(self.log_dir):
            pass
        # Nếu CHƯA tồn tại -> Tạo file và ghi dòng Header (Tiêu đề cột: Time, Machine, Model, OK, NG...)
        
        # 5. Mở file ở chế độ 'a' (Append - Ghi nối tiếp)
        # Rút các số liệu từ parsed_data ra, ghép thành 1 chuỗi cách nhau bằng dấu phẩy
        # Cấu trúc 1 dòng JSON ghi xuống file
        log_data = {
            "message": parsed_data
        }
        with open(filename, "a", encoding="utf-8") as f:
        # Ghi dưới dạng JSON Lines (mỗi đối tượng JSON là 1 dòng)
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        pass