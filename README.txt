Dùng lệnh này để đóng gói lại nếu sửa code 
pyinstaller --onefile --noconsole --paths="." --add-data "Backend\config.json;Backend" UI\main.py
nếu lỗi venv
python -m PyInstaller --onefile --noconsole --paths="." --add-data "Backend\config.json;Backend" UI\main.py

link QT designer nếu mất
...\.venv311\Lib\site-packages\qt5_applications\Qt\bin

cần sửa
- Chỉnh chỗ gửi data lên sql, nó phải thuộc hàm send ms đúng (ưu tiên 3)
- gửi data lên sql đng hiển thị sai, trên txt_log_rcv_server , cần hiển thị trên txt_log_send_server (ưu tiên 1)
- 
