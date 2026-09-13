import json
import os
import requests
import threading
import time
from datetime import datetime
from typing import Optional, Dict

class DataParserModel:

    def __init__(self, prefix=""):
        self.prefix = prefix
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


    def parse_csv(self, raw_data) -> Optional[Dict[str, str]]:
        try: 
            # Ví dụ raw_data = "DRB_02,A175,1000,900,100,90,1,2025-12-12,2025-12-12 09:09:10"
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
                    parts.append(day)    
                    parts.append(f"{day} {hour}")  
                    
                    # 2. Ráp dữ liệu dựa theo "mapping" trong config
                    extracted_data = {}
                    mapping = val.get("mapping")
                    
                    for index_str, field_name in mapping.items():
                        idx = int(index_str) # Chuyển "0", "1" thành số nguyên
                        if idx < len(parts):
                            extracted_data[field_name] = parts[idx]

                    print(f"extracted_data: {extracted_data}")
                    

                    return extracted_data # Gọi 1 lần duy nhất và trả về kết quả
                    {'machine': 'DRB_02', 'model': 'A175', 'total': '1000', 'qtyOk': '650',
                      'qtyNg': '350', 'rate': '65', 'shifts': '1', 'date': '2025-12-12', 'time': '2025-12-12 09:09:10', 'message':'wait_material'}
            print(f"{self.prefix} Chuỗi không chứa từ khóa hợp lệ")    
            return None  # Chuỗi không chứa từ khóa hợp lệ
            
        except Exception as e:
            print(f"[DataParser] Lỗi phân tích dữ liệu: {e}")
            return None 

    # def _save_to_json(self):
    #     # tao file json(vd: log_2026-08-30.json)
    #     today_str = datetime.now().strftime("%Y-%m-%d")

    #     dir = os.path.dirname(os.path.abspath(__file__))
    #     parent_dir = os.path.dirname(dir)
    #     filename = os.path.join(parent_dir, f"log_{today_str}.json")

    #     # Cấu trúc 1 dòng JSON ghi xuống file
    #     log_data = {
    #         "message": self.extracted_data
    #     }

    #     # GHi log: Dùng Lock để đảm bảo an toàn khi các luồng ngầm ghi file cùng lúc
    #     with self.lock:
    #         with open(filename, "a", encoding="utf-8") as f:
    #             # Ghi dưới dạng JSON Lines (mỗi đối tượng JSON là 1 dòng)
    #             f.write(json.dumps(log_data, ensure_ascii=False) + "\n")

    # def _send_to_api(self):
    #     url = "http://192.168.130.236:8010/Product"
        
    #     headers = {
    #         "Connection": "Keep-Alive",
    #         "Content-Type": "application/json",
    #         "User-Agent": "CTC_Client/1.0"
    #         # Content-Length và Host: thư viện requests tự điền, không cần khai báo
    #     }
        
    #     # Ép kiểu đúng định dạng IT yêu cầu trước khi gửi
    #     payload = {
    #         "machine" : str(self.extracted_data.get("machine", "")),
    #         "model"   : str(self.extracted_data.get("model", "")),
    #         "total"   : int(self.extracted_data.get("total", 0)),
    #         "qtyOk"   : int(self.extracted_data.get("qtyOk", 0)),
    #         "qtyNg"   : int(self.extracted_data.get("qtyNg", 0)),
    #         "rate"    : float(self.extracted_data.get("rate", 0.0)),
    #         "shifts"  : str(self.extracted_data.get("shifts", "")),
    #         "date"    : datetime.now().strftime("%Y-%m-%d"),
    #         "time"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     }

    #     try:
            
    #         response = requests.post(url, json=payload, headers=headers, timeout=5)
            
    #         if response.status_code == 201:
    #             self.data_rcv_SQL = (
    #                 f"{self.prefix} [API] Server trả về: "
    #                 f"{response.status_code} - {response.text}"
    #             )
    #             return self.data_rcv_SQL
    #         else:
    #             self.data_rcv_SQL = (
    #                 f"{self.prefix} [API] Gửi SQL thất bại: "
    #                 f"{response.status_code} - {response.text}"
    #             )   
    #             return self.data_rcv_SQL        
                            
    #     except requests.exceptions.ConnectionError:
    #         self.data_rcv_SQL = (f"{self.prefix} [API] Loi: Khong ket noi duoc toi server IT")
    #         return self.data_rcv_SQL   
            
    #     except requests.exceptions.Timeout:
    #         self.data_rcv_SQL = (f"{self.prefix} [API] Loi: Server IT khong phan hoi (timeout 5s)")
    #         return self.data_rcv_SQL 
    #     except Exception as e:
    #         self.data_rcv_SQL = (f"{self.prefix} [API] Loi khong xac dinh: {e}")
    #         return self.data_rcv_SQL

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
    parser = DataParserModel(config_data.get("parser_rules", {}))
    
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
