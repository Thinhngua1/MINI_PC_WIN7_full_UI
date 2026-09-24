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

        # ====== Tránh lưu đề file data khi restart app ======
        today_file = self.get_today_file_path()
        if os.path.exists(today_file):
            try:
                import json # (Nếu ở đầu file chưa import json thì thêm vào nhé)
                with open(today_file, 'r', encoding='utf-8') as f:
                    self.daily_data = json.load(f) # Nơi chứa Data thực tế của tất cả các máy
                print("Da khoi phuc thanh cong du lieu tu o cung!")
            except Exception as e:
                print(f"Loi doc file luc khoi dong: {e}")
                self.daily_data = {} 

        else: 
            self.daily_data = {} 
        # ====================================================

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

            # ========== THÊM BỘ LỌC CHỐNG GHI ĐÈ SỐ 0 ===========
            new_total = int(counters.get("total", 0))
            
            # Lấy số liệu cũ đang có trong RAM (vừa đọc từ ổ cứng lên)
            old_data = self.daily_data[machine_id]["Hourly"].get(hour_str, {})
            old_total = int(old_data.get("total", 0))
            
            # Nếu thẻ máy chưa nhận được data từ Robot (new_total = 0)
            # mà trong RAM đang có số thật (old_total > 0), thì BỎ QUA không ghi đè!
            if new_total == 0 and old_total > 0:
                continue 
            # =====================================================

            # Cập nhật số liệu vào đúng khung giờ (hour_str phải khớp VD "08:00")
            if hour_str in self.daily_data[machine_id]["Hourly"]:
                self.daily_data[machine_id]["Hourly"][hour_str] = counters
        
        self.save_to_disk()

        print(f"Da luu Snapshot {hour_str}. Dang ban sang UI de refresh")
        
        # ============ THÊM ĐOẠN NÀY ĐỂ UI TỰ REFRESH ============
        table_rows = []
        hours_order = [f"{h:02d}:00" for h in range(8, 24)] + [f"{h:02d}:00" for h in range(0, 8)]

        # tạo list 2D cho bảng ŨI
        for machine_id, hourly_data in self.daily_data.items():
            row_data = [machine_id]
            sum_total_day = 0
            dict_hour = hourly_data.get("Hourly", {})
            
            prev_accumulated = 0  # Biến nhớ số tích lũy của giờ trước đó
            
            for hour in hours_order:
                # 1. Kiểm tra xem đã có dữ liệu của giờ này chưa (tránh giờ tương lai)
                if hour in dict_hour:
                    current_accumulated = int(dict_hour[hour].get("total", 0))
                    
                    # 2. Xử lý phép trừ
                    if current_accumulated >= prev_accumulated:
                        actual_hourly = current_accumulated - prev_accumulated
                    else:
                        # TRƯỜNG HỢP NGOẠI LỆ: Robot bị reset ca hoặc khởi động lại (số bị tụt)
                        # Lúc này sản lượng giờ chính là số mới luôn, không trừ nữa
                        actual_hourly = current_accumulated
                        
                    # Lưu mốc hiện tại thành "quá khứ" để dành cho vòng lặp giờ tiếp theo
                    prev_accumulated = current_accumulated
                else:
                    # Chưa tới giờ này, hiển thị 0
                    actual_hourly = 0
                    
                # 3. Cộng dồn vào cột TOTAL cuối cùng và nhét vào mảng
                sum_total_day += actual_hourly
                row_data.append(str(actual_hourly))
                
            # Cột cuối cùng là tổng thực tế trong ca
            row_data.append(str(sum_total_day))
            table_rows.append(row_data)
            
        # Bắn mảng 2 chiều vừa tạo sang cho MainWindow vẽ lại
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.signal_table_data_ready.emit(True, f"{today_str} | REALTIME UPDATE", table_rows)

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
                    quantity_of_hour = int(quantity["total"])
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


        
