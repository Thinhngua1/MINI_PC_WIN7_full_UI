import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
from datetime import datetime

# 1. Dán đường link Webhook của em vào đây
webhook_url = "https://default9b3519dd51ef4d4cbac3abb36b7c63.58.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/14/workflows/5c5afdc4b48045aaaf12ab25bcc2c51f/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=TIExcsFU5zbd7-uBuCuyV9b8-i4o0rkVUUe_B26xrC0"

# Lấy giờ hiện tại
now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# 2. Tạo nội dung thẻ (Adaptive Card) giống hệt cấu trúc ảnh mẫu của em
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
                        "text": "📊 **Báo cáo sản lượng test thử**",
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
                        "facts": [
                            {"title": "DRB_01", "value": "⚠️ N/A (Offline)"},
                            {"title": "DRB_02", "value": "✅ 150/150 (Running)"}
                        ]
                    }
                ]
            }
        }
    ]
}

# 3. Gửi gói tin đi
print("Đang gửi tin nhắn lên Teams...")
response = requests.post(
    webhook_url, 
    headers={'Content-Type': 'application/json'}, 
    data=json.dumps(card_payload)
)

# 4. Kiểm tra kết quả
if response.status_code == 202 or response.status_code == 200:
    print("✅ Bắn tin nhắn thành công! Mở Teams lên check")
else:
    print("❌ Lỗi:", response.status_code, response.text)


if __name__ == "__main__":
    pass