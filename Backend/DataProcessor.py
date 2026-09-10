import json
import os
import requests
import threading
import time
from datetime import datetime

class DataProcessor:

    def __init__(self, prefix=""):
        self.prefix = prefix
        # Đọc file config một lần duy nhất lúc khởi động app
        try:
            #lay path config file
            this_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(this_dir, "config.json")

            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            print("Lỗi đọc file config SQL:", e)
            self.config = {}

        # ghi log
        self.dir = os.path.dirname(os.path.abspath(__file__))

        # Khóa an toàn khi có nhiều luồng (thread) cùng gọi hàm print
        self.lock = threading.Lock()


    def process_and_send(self, raw_data):
        try: 
            # Ví dụ raw_data = "DRB_02,A175,1000,900,100,90,1,2025-12-12,2025-12-12 09:09:10"
            # 1. Quét qua các cấu hình máy để tìm xem chuỗi này của máy nào
            for _, val in self.config.items():
                keyword = val.get("keyword")
                
                # Nếu tìm thấy từ khóa trong chuỗi
                if raw_data.startswith(keyword):
                    #bổ sung ngày h
                    day = datetime.now().strftime("%Y-%m-%d")
                    hour = datetime.now().strftime("%H:%M:%S")

                    # Cắt chuỗi và loại bỏ khoảng trắng dư thừa
                    parts = [p.strip() for p in raw_data.split(",")]    
                    parts.append(day)    
                    parts.append(f"{day} {hour}")  
                    
                    # 2. Ráp dữ liệu dựa theo "mapping" trong config
                    self.extracted_data = {}
                    mapping = val.get("mapping")
                    
                    for index_str, field_name in mapping.items():
                        idx = int(index_str) # Chuyển "0", "1" thành số nguyên
                        if idx < len(parts):
                            self.extracted_data[field_name] = parts[idx]
                    # GỌI HÀM GỬI SQL
                                        
                    print(f"{self.prefix} [DataProcessor] Chuẩn bị data và gửi SQL: {self.extracted_data}")
                    self._save_to_json()
                    
                    return self._send_to_api() # Gọi 1 lần duy nhất và trả về kết quả
                
            print(f"{self.prefix} Chuỗi không chứa từ khóa hợp lệ")    
            return False # Chuỗi không chứa từ khóa hợp lệ
            
        except Exception as e:
            print(f"{self.prefix} Processor data fail")

    def _save_to_json(self):
        # tao file json(vd: log_2026-08-30.json)
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.dir, f"log_{today_str}.json")

        # Cấu trúc 1 dòng JSON ghi xuống file
        log_data = {
            "message": self.extracted_data
        }

        # GHi log: Dùng Lock để đảm bảo an toàn khi các luồng ngầm ghi file cùng lúc
        with self.lock:
            with open(filename, "a", encoding="utf-8") as f:
                # Ghi dưới dạng JSON Lines (mỗi đối tượng JSON là 1 dòng)
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

    def _send_to_api(self):
        url = "http://192.168.130.236:8010/Product"
        
        headers = {
            "Connection": "Keep-Alive",
            "Content-Type": "application/json",
            "User-Agent": "CTC_Client/1.0"
            # Content-Length và Host: thư viện requests tự điền, không cần khai báo
        }
        
        # Ép kiểu đúng định dạng IT yêu cầu trước khi gửi
        payload = {
            "machine" : str(self.extracted_data.get("machine", "")),
            "model"   : str(self.extracted_data.get("model", "")),
            "total"   : int(self.extracted_data.get("total", 0)),
            "qtyOk"   : int(self.extracted_data.get("qtyOk", 0)),
            "qtyNg"   : int(self.extracted_data.get("qtyNg", 0)),
            "rate"    : float(self.extracted_data.get("rate", 0.0)),
            "shifts"  : str(self.extracted_data.get("shifts", "")),
            "date"    : datetime.now().strftime("%Y-%m-%d"),
            "time"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 201:
                self.data_rcv_SQL = (
                    f"{self.prefix} [API] Server trả về: "
                    f"{response.status_code} - {response.text}"
                )
                return self.data_rcv_SQL
            else:
                self.data_rcv_SQL = (
                    f"{self.prefix} [API] Gửi SQL thất bại: "
                    f"{response.status_code} - {response.text}"
                )   
                return self.data_rcv_SQL        
                            
        except requests.exceptions.ConnectionError:
            self.data_rcv_SQL = (f"{self.prefix} [API] Loi: Khong ket noi duoc toi server IT")
            return self.data_rcv_SQL   
            
        except requests.exceptions.Timeout:
            self.data_rcv_SQL = (f"{self.prefix} [API] Loi: Server IT khong phan hoi (timeout 5s)")
            return self.data_rcv_SQL 
        except Exception as e:
            self.data_rcv_SQL = (f"{self.prefix} [API] Loi khong xac dinh: {e}")
            return self.data_rcv_SQL