Dùng lệnh này để đóng gói lại nếu sửa code 
python -m PyInstaller --onefile --noconsole --add-data "config;config" --add-data "views;views" main.py
python -m PyInstaller --onefile  --add-data "config;config" --add-data "views;views" main.py

link QT designer nếu mất
...\.venv311\Lib\site-packages\qt5_applications\Qt\bin

cần sửa

- 
