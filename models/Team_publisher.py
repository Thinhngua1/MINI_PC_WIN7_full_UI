import os
import requests
import json
import sys
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class TeamWorker(QThread):
    """Luồng phụ để gửi HTTP Request mà không làm đơ UI"""
    signal_result = pyqtSignal(bool, str)

    def __init__(self, webhook_url, payload):
        super().__init__()
        self.webhook_url = webhook_url
        self.payload = payload

    def run(self):
        try:
            response = requests.post(
                self.webhook_url, 
                headers={'Content-Type': 'application/json'}, 
                data=json.dumps(self.payload)
            )
            if response.status_code in [200, 202]:
                self.signal_result.emit(True, "Gửi Teams thành công")
            else:
                self.signal_result.emit(False, f"Lỗi HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.signal_result.emit(False, f"Lỗi Exception: {str(e)}")

class TeamPublisher(QObject):
    def __init__(self):
        super().__init__()
        self.webhook_url = ""
        self.load_webhook_from_security()

    def load_webhook_from_security(self):

        # Cấu hình đường dẫn thông minh: Chấp cả lúc chạy code Python lẫn lúc chạy file .exe
        if getattr(sys, 'frozen', False):
            # Nếu là file .exe, tìm thư mục security nằm ngay cạnh file .exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Nếu chạy trên VS Code, lùi ra 1 cấp từ thư mục models
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)
            
        secret_path = os.path.join(base_dir, "security", "secrets.json")

        if os.path.exists(secret_path):
            try:
                with open(secret_path, "r", encoding="utf-8") as f:
                    secret_data = json.load(f)
                    self.webhook_url = secret_data.get("teams_webhook", "")
            except Exception as e:
                print(f"Lỗi đọc file secrets.json: {e}")
        else:
            print(f"Cảnh báo: Không tìm thấy file bảo mật tại {secret_path}")

    def send_report(self, title, machine_data_list):
        """
        machine_data_list là 1 list các dict: [{"name": "DRB_01", "status": "⚠️ N/A (Offline)"}, ...]
        """
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Đúc các máy thành danh sách facts cho Adaptive Card( Form trình bày tin nhắn, gốc bắt đầu từ Json)
        facts = []
        for machine in machine_data_list:
            facts.append({
                "title": machine["name"],
                "value": machine["status"]
            })

        card_payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": f"📊 **{title}**",
                                "size": "Medium",
                                "weight": "Bolder"
                            },
                            {
                                "type": "TextBlock",
                                "text": now_str,
                                "isSubtle": True,
                                "spacing": "None"
                            },
                            {
                                "type": "FactSet",
                                "facts": facts
                            }
                        ]
                    }
                }
            ]
        }

        # Khởi chạy luồng gửi tin
        self.worker = TeamWorker(self.webhook_url, card_payload)
        self.worker.signal_result.connect(self._on_send_finished)
        self.worker.start()

    def _on_send_finished(self, success, message):
        # Có thể in ra log ở đây
        if success:
            print(f"[TeamPublisher] {message}")
        else:
            print(f"[TeamPublisher] {message}")