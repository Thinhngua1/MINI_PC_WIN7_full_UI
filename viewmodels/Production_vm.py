import os
import json
import copy
import sys
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class ProductionViewModel(QObject):

    # Signal trả về: (Thành công hay không?,thông báo)
    signal_table_data_ready = pyqtSignal(bool, str, list) # [ ["LINE 01", "10", "20", ...], ["LINE 02", "0", "5", ...] ]

    def __init__(self):
        super().__init__()
        self.frame = {
            "Shift_1_Total": 0,
            "Shift_2_Total": 0,
            "Hourly": {
                "08:00": {"ok": 0, "ng": 0,"total":0},
                "09:00": {"ok": 0, "ng": 0,"total":0},
                "10:00": {"ok": 0, "ng": 0,"total":0},
                "11:00": {"ok": 0, "ng": 0,"total":0},
                "12:00": {"ok": 0, "ng": 0,"total":0},
                "13:00": {"ok": 0, "ng": 0,"total":0},
                "14:00": {"ok": 0, "ng": 0,"total":0},
                "15:00": {"ok": 0, "ng": 0,"total":0},      
                "16:00": {"ok": 0, "ng": 0,"total":0},
                "17:00": {"ok": 0, "ng": 0,"total":0},
                "18:00": {"ok": 0, "ng": 0,"total":0},
                "19:00": {"ok": 0, "ng": 0,"total":0},           
                "20:00": {"ok": 0, "ng": 0,"total":0},
                "21:00": {"ok": 0, "ng": 0,"total":0},
                "22:00": {"ok": 0, "ng": 0,"total":0},
                "23:00": {"ok": 0, "ng": 0,"total":0},                 
                "00:00": {"ok": 0, "ng": 0,"total":0},
                "01:00": {"ok": 0, "ng": 0,"total":0},
                "02:00": {"ok": 0, "ng": 0,"total":0},                 
                "03:00": {"ok": 0, "ng": 0,"total":0},
                "04:00": {"ok": 0, "ng": 0,"total":0},
                "05:00": {"ok": 0, "ng": 0,"total":0},                 
                "06:00": {"ok": 0, "ng": 0,"total":0},
                "07:00": {"ok": 0, "ng": 0,"total":0}
            }
        }

        self.daily_data = {} # Nơi chứa Data thực tế của tất cả các máy
        
        # --- KIỂM TRA MÔI TRƯỜNG CHẠY ĐỂ TÌM ĐƯỜNG DẪN GỐC ---
        if getattr(sys, 'frozen', False):
            # Đang chạy dưới dạng file .exe đã đóng gói
            # Trỏ thẳng ra thư mục đang chứa file main.exe
            parent_dir = os.path.dirname(sys.executable)
        else:
            # Đang chạy bằng code python thô (khi dev)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
        self.log_dir = os.path.join(parent_dir, "LOG")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def get_today_file_path(self):
        """Tự động tạo tên file theo ngày hôm nay (VD: production_2026-09-15.json)"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"production_{today_str}.json")
    
    # Hàm HỨNG SIGNAL từ trạm đấu dây
    def save_hourly_snapshot(self, hour_str, snapshot_data):
        print(f"[Production] Nhận snapshot lúc {hour_str}, đang lưu...")
        
        for machine_id, counters in snapshot_data.items():
            if machine_id not in self.daily_data:
                # Dùng copy.deepcopy để nhân bản cái frame gốc ra cho từng máy mới
                self.daily_data[machine_id] = copy.deepcopy(self.frame)
            
            # Cập nhật số liệu vào đúng khung giờ (hour_str phải khớp VD "08:00")
            if hour_str in self.daily_data[machine_id]["Hourly"]:
                self.daily_data[machine_id]["Hourly"][hour_str] = counters
        
        self.save_to_disk()

    def save_to_disk(self):
        """Ghi xuống ổ cứng"""
        file_path = self.get_today_file_path()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.daily_data, f, indent=4)

    def load_data_by_date(self, date_str):
        """Hàm đọc file khi MainWindow yêu cầu"""
        file_path = os.path.join(self.log_dir, f"production_{date_str}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # --- VIEWMODEL TỰ NHAI DATA ---
            table_rows = []
            
            for machine_id, hourly_data in data.items():
                sum_total_day = 0
                row_data = [machine_id]
                
                # Lặp qua các khung giờ để lôi con số ra (đã làm tròn/format nếu cần)
                dict_hour = hourly_data["Hourly"]
                for _,quantity in dict_hour.items():
                    quantity_of_hour = quantity["total"]
                    sum_total_day += quantity_of_hour

                    row_data.append(quantity_of_hour)

                # Cột 26: Thêm tổng cả ngày vào cuối cùng
                row_data.append(str(sum_total_day))

                # tạo list 2D full line
                table_rows.append(row_data)
                
            self.signal_table_data_ready.emit(True, f"{date_str} | Tải dữ liệu thành công.", table_rows)                
            # Chỉ ném Mảng 2 chiều của biểu đồ sang cho View

        else:
            self.signal_table_data_ready.emit(False, f"{date_str} | Không có dữ liệu lịch sử.", {})


        
