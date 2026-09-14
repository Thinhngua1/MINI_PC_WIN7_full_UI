import requests
import os
import json
from datetime import datetime
from PyQt5.QtCore  import QObject, pyqtSignal

class ApiPublisherModel(QObject):
    signal_log_updated = pyqtSignal(str)

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
        

    def _send_to_api(self,extracted_data):
        # url = "http://192.168.130.236:8010/Product"
        url = self.config["sql_server"]['api_endpoint']
        
        headers = {
            "Connection": "Keep-Alive",
            "Content-Type": "application/json",
            "User-Agent": "CTC_Client/1.0"
            # Content-Length và Host: thư viện requests tự điền, không cần khai báo
        }
        
        # Ép kiểu đúng định dạng IT yêu cầu trước khi gửi
        payload = {
            "machine" : str(extracted_data.get("machine", "")),
            "model"   : str(extracted_data.get("model", "")),
            "total"   : int(extracted_data.get("total", 0)),
            "qtyOk"   : int(extracted_data.get("qtyOk", 0)),
            "qtyNg"   : int(extracted_data.get("qtyNg", 0)),
            "rate"    : float(extracted_data.get("rate", 0.0)),
            "shifts"  : str(extracted_data.get("shifts", "")),
            "date"    : datetime.now().strftime("%Y-%m-%d"),
            "time"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 201:
                self.data_rcv_SQL = (
                    f"[API] Server trả về: "
                    f"{response.status_code} - {response.text}"
                )
                print(self.data_rcv_SQL)
                self.signal_log_updated.emit(self.data_rcv_SQL) # send to UI
                return self.data_rcv_SQL
            else:
                self.data_rcv_SQL = (
                    f"[API] Gửi SQL thất bại: "
                    f"{response.status_code} - {response.text}"
                )   
                print(self.data_rcv_SQL)
                self.signal_log_updated.emit(self.data_rcv_SQL) # send to UI
                return self.data_rcv_SQL        
                                       
        except requests.exceptions.ConnectionError:
            self.data_rcv_SQL = (f"[API] Loi: Khong ket noi duoc toi server IT")
            return self.data_rcv_SQL   
            
        except requests.exceptions.Timeout:
            self.data_rcv_SQL = (f"[API] Loi: Server IT khong phan hoi (timeout 5s)")
            return self.data_rcv_SQL 
        except Exception as e:
            self.data_rcv_SQL = (f"[API] Loi khong xac dinh: {e}")
            return self.data_rcv_SQL
