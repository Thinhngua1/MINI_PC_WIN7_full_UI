import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QTreeWidgetItem, QTableWidgetItem, QButtonGroup, QAbstractItemView
from PyQt5 import uic
from PyQt5.QtCore import Qt,QDate, pyqtSignal,QEvent

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout
from views.machine_dashboard_dialog import MachineDashboardDialog
from views.global_alarms_dialog import GlobalAlarmsDialog


class MainWindow(QMainWindow):

    # signal button "tải dữ liệu"
    signal_request_load_data = pyqtSignal(str)

    def __init__(self, dashboard_vm):
        super().__init__()
        # Load file UI tổng
        ui_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        uic.loadUi(ui_path, self)

        # Lưu ViewModel
        self.dashboard_vm = dashboard_vm
        
        # Dictionary chứa các tham chiếu đến UI của từng máy để dễ dàng update (Card UI)
        self.machine_cards = {}
            # Map widget → machine_id để eventFilter tra nhanh
        self._widget_to_machine = {}

        # Ghi nhớ Tab đang mở mặc định để lọc UI
        self.current_line_filter = "Change Tray"

        # 1. Khởi tạo danh sách máy động
        self.setup_dynamic_machines()

        # 1.5. Cài đặt Cây Menu (Tree Menu)
        self.setup_tree_menu()

        # 3. Khởi tạo giao diện Bảng
        self.setup_production_table()
        
        # Móc nối nút bấm Bảng tổng hợp lỗi 
        self.btn_alarm_total.clicked.connect(self.open_global_alarms)
        
        # 4. 
        # Bật chế độ "Công tắc" cho 2 nút
        self.btn_chart_line.setCheckable(True)
        self.btn_chart_bar.setCheckable(True)
        # Nhét 2 nút vào chung 1 Group để tự động tắt bật chéo nhau
        self.chart_btn_group = QButtonGroup(self)
        self.chart_btn_group.addButton(self.btn_chart_line)
        self.chart_btn_group.addButton(self.btn_chart_bar)
        # Mặc định chọn nút ĐƯỜNG cho nó sáng lên
        self.btn_chart_line.setChecked(True)

        # 4. Khởi tạo giao diện Biểu đồ (CẬU THÊM DÒNG NÀY VÀO LÀ HẾT LỖI)
        self.setup_chart_canvas() 

        # 2. Đấu nối các tín hiệu (Wiring Signals)
        self.wire_signals()

        
    def setup_dynamic_machines(self):
        """Khởi tạo giao diện động dựa trên danh sách line trong ViewModel."""
        card_ui_path = os.path.join(os.path.dirname(__file__), 'line_card.ui')
        
        row, col = 0, 0
        max_col = 4 # 
        
        # Duyệt qua các LineViewModel đã được tạo trong DashboardViewModel
        for machine_id, line_vm in self.dashboard_vm.lines.items():
            # Load template card 
            card_widget = QWidget()
            uic.loadUi(card_ui_path, card_widget)

            # 1. KHÓA KÍCH THƯỚC: Ép thẻ không được phình to ra
            card_widget.setFixedSize(card_widget.size())
            
            # Gán giá trị ban đầu cho UI Card
            self.update_card_ui(card_widget, line_vm)

            # Thêm card vào Grid Layout của ScrollArea
            self.gridLayout_machines.addWidget(card_widget, row, col)
            
            # Lưu lại reference để update sau này
            self.machine_cards[machine_id] = card_widget

            # Gắn sự kiện click: mở Sub-Dashboard popup khi user click vào thẻ
            # Gắn event filter lên card VÀ toàn bộ widget con bên trong
            self._widget_to_machine[card_widget] = machine_id
            card_widget.installEventFilter(self)


            # Nối tín hiệu từ LineViewModel vào Slot update của View
            line_vm.signal_update_ui.connect(lambda card=card_widget, vm=line_vm: self.update_card_ui(card, vm))

            col += 1
            if col >= max_col:
                col = 0
                row += 1

        # DỒN LAYOUT: Ép toàn bộ các thẻ dồn lên góc Trên - Bên Trái, không bị dãn khoảng cách
        self.gridLayout_machines.setRowStretch(99, 1)
        self.gridLayout_machines.setColumnStretch(99, 1)
        

    def setup_tree_menu(self):
        """Tạo cấu trúc nhánh cây (Style CSS đã được chuyển sang Qt Designer)"""
        
        # Xây dựng các nhánh cây bằng code (nhàn hơn kéo thả UI nhiều)
        item_line_monitor = QTreeWidgetItem(self.tree_menu, ["Overview"])
        QTreeWidgetItem(item_line_monitor, ["Change Tray"])
        QTreeWidgetItem(item_line_monitor, ["Function"])
        QTreeWidgetItem(item_line_monitor, ["AUTOTAPE"])
        QTreeWidgetItem(item_line_monitor, ["MEDITECH"])
        QTreeWidgetItem(item_line_monitor, ["PRESSTAPE"])
        QTreeWidgetItem(item_line_monitor, ["CTC"])
        QTreeWidgetItem(item_line_monitor, ["X-RAY"])

        
        QTreeWidgetItem(self.tree_menu, ["Equipment"])
        QTreeWidgetItem(self.tree_menu, ["Alarm History"])
        QTreeWidgetItem(self.tree_menu, ["Production"])
        QTreeWidgetItem(self.tree_menu, ["Quality"])
        QTreeWidgetItem(self.tree_menu, ["Energy Monitor"])
        QTreeWidgetItem(self.tree_menu, ["Trend"])
        QTreeWidgetItem(self.tree_menu, ["Data Log"])
        QTreeWidgetItem(self.tree_menu, ["SQL_server"])
        
        # Mở sẵn nhánh Line Monitor
        item_line_monitor.setExpanded(True)

    def wire_signals(self):
        """Đấu nối các tín hiệu tổng của Dashboard."""
        self.dashboard_vm.signal_summary_updated.connect(self.update_summary_ui)
        
        # Chuyển trang UI khi bấm nút ở Cây Menu
        self.tree_menu.itemClicked.connect(self.handle_tree_menu_click)
        
        # Đặt trang mặc định là Line Monitor
        self.stackedWidget.setCurrentIndex(0)

        # event bấm nút "Tải dữ liệu"
        self.btn_load_data.clicked.connect(self.on_btn_load_clicked)

        # event vẽ biểu đồ
            # 1. Khi User click vào 1 ô bất kỳ trên bảng -> Gọi hàm lôi data ra vẽ
        self.tbl_production.itemClicked.connect(self.on_table_row_clicked)
        
            # 2. Khi User đổi chế độ ĐƯỜNG / CỘT -> Vẽ lại (dùng data đang lưu trong cache)
        self.btn_chart_line.clicked.connect(lambda: self.draw_production_chart(self.current_machine, self.current_x, self.current_y))
        self.btn_chart_bar.clicked.connect(lambda: self.draw_production_chart(self.current_machine, self.current_x, self.current_y))

    def handle_tree_menu_click(self, item, column=0):
        """Xử lý khi user bấm vào bất kỳ thẻ nào trên cây Menu"""
        menu_name = item.text(0)
        
        # Bấm vào chữ mẹ thì tự Xổ/Thu
        if menu_name == "Line Monitor":
            item.setExpanded(not item.isExpanded())
            return

        Overview = {
            "Change Tray": 0,
            "Function": 0,
            "AUTOTAPE":0,
            "MEDITECH":0,
            "PRESSTAPE":0,
            "CTC":0,
            "X-RAY":0}
        page_map = {
            "Change Tray": 0,
            "Function": 0,
            "AUTOTAPE":0,
            "MEDITECH":0,
            "PRESSTAPE":0,
            "CTC":0,
            "X-RAY":0,
            "Equipment": 1,
            "Alarm History": 2,
            "Production": 3,
            "Quality": 4,
            "Energy Monitor": 5,
            "Trend": 6,
            "Data Log": 7,
            "SQL_server": 8
        }
        
        if menu_name in page_map:
            self.stackedWidget.setCurrentIndex(page_map[menu_name])

            if menu_name in Overview:
                print(f"[UI] Đang xem Line Monitor chế độ: {menu_name}")

                # Lưu lại Tab đang xem
                self.current_line_filter = menu_name
                # Quét toàn bộ thẻ máy đang có trên màn hình
                for machine_id, card_widget in self.machine_cards.items():
                    # Lấy dữ liệu type hiện tại của máy đó từ ViewModel

                    current_type = str(getattr(self.dashboard_vm.lines[machine_id], 'type', '') or "").strip().lower()
                    current_filter = str(getattr(self, 'current_line_filter', None)).strip().lower()
                    
                    line_monitor_modes =["change tray", "function", "autotape", "meditech", "presstape", "ctc", "x-ray"]
                    
                    # đứng ở bất kỳ Tab nào thuộc Line Monitor, phải check ẩn/hiện liên tục
                    if current_filter in line_monitor_modes:
                        if current_type == current_filter:
                            card_widget.setVisible(True)
                        else:
                            card_widget.setVisible(False)

    def append_sql_log(self, message: str):
        """Nhận log từ các Model (TCP, Parser, API) và hiển thị lên txt_sql_log."""
        self.txt_sql_log.append(str(message))
        

    def update_card_ui(self, card_widget, line_vm):
        """Hàm nhận tín hiệu và cập nhật một card máy cụ thể."""
        # Gom Tên Máy - Tên Model - Trạng Thái lên cùng 1 dòng
        card_widget.lbl_machine_id.setText(f"{line_vm.machine_id} - {line_vm.machine_model} - {line_vm.status}")
        
        card_widget.lbl_ok_count.setText(str(line_vm.ok_count))
        card_widget.lbl_ng_count.setText(str(line_vm.ng_count))
        card_widget.lbl_total_count.setText(str(line_vm.total_count))
        card_widget.lbl_rate.setText(f"{line_vm.rate}%")

        # --- LOGIC TỰ BỐC HƠI KHI ROBOT ĐỔI TYPE ---
        # Lấy type mới nhất vừa được cập nhật, gọt dấu cách
        current_type = str(getattr(line_vm, 'type', '') or "").strip().lower()
        current_filter = str(getattr(self, 'current_line_filter', '')).strip().lower()
        
        # Nếu đang đứng ở màn hình Line Monitor thì kiểm tra để Ẩn/Hiện thẻ ngay lập tức
        if current_filter in ["change tray", "function"]:
            if current_type == current_filter:
                card_widget.setVisible(True)
            else:
                card_widget.setVisible(False)

        #update time of OEE
        # Hàm con: Biến đổi giây (vd: 125s) thành chuỗi (vd: "00:02:05")
        def format_sec(seconds):
            h, rem = divmod(seconds, 3600)
            m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        # Bơm data cho hộp DAY SHIFT
        card_widget.lbl_day_idle.setText(format_sec(line_vm.day_idle_time))
        card_widget.lbl_day_loss.setText(format_sec(line_vm.day_loss_time))
        card_widget.lbl_day_error.setText(format_sec(line_vm.day_error_time))

        # Bơm data cho hộp NIGHT SHIFT
        card_widget.lbl_night_idle.setText(format_sec(line_vm.night_idle_time))
        card_widget.lbl_night_loss.setText(format_sec(line_vm.night_loss_time))
        card_widget.lbl_night_error.setText(format_sec(line_vm.night_error_time))

    def open_machine_dashboard(self, machine_id):
        """Mở Sub-Dashboard popup khi user click vào thẻ máy."""
        line_vm = self.dashboard_vm.lines.get(machine_id)
        if line_vm is None:
            return
        dialog = MachineDashboardDialog(line_vm, parent=self)
        dialog.setWindowTitle(f"Machine Dashboard - {machine_id}")
        dialog.exec_()   # Modal: chặn lại cho đến khi user đóng

    def open_global_alarms(self):
        """Mở Popup Bảng Lỗi Toàn Nhà Máy."""
        dialog = GlobalAlarmsDialog(self.dashboard_vm, self)
        dialog.exec_()

    def update_summary_ui(self, summary_data):      
        """Cập nhật phần Summary chung ở trên cùng."""
        self.lbl_sum_total.setText(str(summary_data['total_machine']))
        self.lbl_sum_running.setText(str(summary_data['machine_running']))
        self.lbl_sum_waiting.setText(str(summary_data['machine_WAITING']))
        self.lbl_sum_alarm.setText(str(summary_data['machine_Alarm']))
        self.lbl_sum_offline.setText(str(summary_data['machine_offline']))
        
        overall_oee = 0.0
        # Cần logic tính OEE từ Model/ViewModel, tạm fix cứng OEE nếu chưa có data
        self.lbl_sum_oee.setText(f"{overall_oee:.1f}%")

    def update_header_time(self, time_str, shift_str):
        self.lbl_DateTime.setText(time_str)
        self.lbl_Shift.setText(shift_str)

    #vẽ bảng cho production Chỉ gọi 1 lần lúc khởi động"""
    def setup_production_table(self): 
        self.date_picker.setDate(QDate.currentDate())  # Set ngày hôm nay

        self.tbl_production.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 1. Danh sách 24 giờ (theo đúng thứ tự trong ảnh: 08:00 -> 07:00)
        hours = [f"{h:02d}:00" for h in range(8, 24)] + \
                [f"{h:02d}:00" for h in range(0, 8)]
        col_headers = ["LINE"] + hours + ["TOTAL"]

        # 2. Danh sách tên máy lấy từ ViewModel (không hardcode)
        machine_ids = list(self.dashboard_vm.lines.keys())

        # 3. Set số cột và số hàng
        self.tbl_production.setColumnCount(len(col_headers))
        self.tbl_production.setRowCount(len(machine_ids))

        # 4. Gán Header cột
        self.tbl_production.setHorizontalHeaderLabels(col_headers)

        # 5. Gán tên máy vào cột đầu tiên (cột LINE)
        for row, machine_id in enumerate(machine_ids):
            item = QTableWidgetItem(machine_id)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.tbl_production.setItem(row, 0, item)

        # 6. Điền số 0 vào tất cả các ô còn lại
        for row in range(len(machine_ids)):
            for col in range(1, len(col_headers)):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                self.tbl_production.setItem(row, col, item)

        # 7. Ép cột LINE cố định nhỏ, các cột giờ bằng nhau
        self.tbl_production.setColumnWidth(0, 80)
        for col in range(1, len(col_headers)):
            self.tbl_production.setColumnWidth(col, 55)

        # 8. Ẩn cột số thứ tự mặc định của Qt
        self.tbl_production.verticalHeader().setVisible(False)



    #============== khối vẽ biểu đồ ======================
    def on_btn_load_clicked(self):
        # Lấy ngày đang chọn và biến thành string chuẩn yyyy-MM-dd
        date_str = self.date_picker.date().toString("yyyy-MM-dd")
        self.signal_request_load_data.emit(date_str)

    #chọn mode vẽ chart
            
        # Bật chế độ "Công tắc" cho 2 nút
        self.btn_chart_line.setCheckable(True)
        self.btn_chart_bar.setCheckable(True)

        # Nhét 2 nút vào chung 1 Group để tự động tắt bật chéo nhau
        self.chart_btn_group = QButtonGroup(self)
        self.chart_btn_group.addButton(self.btn_chart_line)
        self.chart_btn_group.addButton(self.btn_chart_bar)

        # Mặc định chọn nút ĐƯỜNG cho nó sáng lên
        self.btn_chart_line.setChecked(True)
    
    def update_production_table(self, is_success, msg, list_2D):
        """Hứng data trả về từ ProductionVM"""
        self.lbl_data_file_status.setText(msg)
        
        if is_success:
            self.lbl_data_file_status.setStyleSheet("color: #00ff00;") # Màu xanh
            row_map = {}
            for r in range(self.tbl_production.rowCount()):
                item = self.tbl_production.item(r, 0)
                if item:
                    row_map[item.text()] = r

            for row_data in list_2D:
                machine_id = str(row_data[0])
                if machine_id in row_map:
                    target_row = row_map[machine_id]
                    for col_idx in range(1, len(row_data)):
                        val_str = str(row_data[col_idx])
                        item = self.tbl_production.item(target_row, col_idx)
                        if item is None:
                            from PyQt5.QtWidgets import QTableWidgetItem
                            from PyQt5.QtCore import Qt
                            new_item = QTableWidgetItem(val_str)
                            new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.tbl_production.setItem(target_row, col_idx, new_item)
                        else:
                            item.setText(val_str)
        else:
            self.lbl_data_file_status.setStyleSheet("color: #ff0000;") # Màu đỏ
            for row in range(self.tbl_production.rowCount()):
                for col in range(1, self.tbl_production.columnCount()):
                    item = self.tbl_production.item(row, col)
                    if item is None:
                        from PyQt5.QtWidgets import QTableWidgetItem
                        from PyQt5.QtCore import Qt
                        new_item = QTableWidgetItem("0")
                        new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tbl_production.setItem(row, col, new_item)
                    else:
                        item.setText("0")

        if hasattr(self, 'current_machine') and self.current_machine:
            # Quét tìm cái máy đang được chọn nằm ở hàng (row) số mấy
            for row in range(self.tbl_production.rowCount()):
                if self.tbl_production.item(row, 0).text() == self.current_machine:
                    
                    # Cào lại 24 cột số liệu mới nhất của hàng đó
                    x_labels, y_values = [], []
                    for col in range(1, 25):
                        x_labels.append(self.tbl_production.horizontalHeaderItem(col).text())
                        val_str = self.tbl_production.item(row, col).text()
                        y_values.append(int(val_str) if val_str.isdigit() else 0)
                    
                    # Ép biểu đồ vẽ lại với data mới chớp nhoáng
                    self.draw_production_chart(self.current_machine, x_labels, y_values)
                    break


    def setup_chart_canvas(self):
        """Biến frame_chart thành một bảng vẽ Matplotlib giao diện Dark Mode"""
        # 1. Tạo Layout nhét vào trong frame_chart
        self.chart_layout = QVBoxLayout(self.frame_chart)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # 2. Khởi tạo Figure (Bảng vẽ) với màu nền tiệp với Dark Theme
        self.figure = Figure(facecolor='#0a141d')
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        
        # 3. Khởi tạo Trục tọa độ (Axes)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#0a141d')
        self.ax.tick_params(colors='white') # Chữ số màu trắng
        
        # 4. Lưu lại 2 biến data tạm để dùng khi bấm nút chuyển ĐƯỜNG/CỘT
        self.current_x = []
        self.current_y = []
        self.current_machine = ""

    def draw_production_chart(self, machine_id, x_labels, y_values):
        """Hàm thực thi vẽ biểu đồ"""
        # Lưu vào cache để xài lại khi user bấm nút gạt Cột/Đường
        self.current_x = x_labels
        self.current_y = y_values
        self.current_machine = machine_id
        
        self.ax.clear() # Xóa nét vẽ cũ
        
        # Kiểm tra xem nút nào đang được bấm
        if self.btn_chart_line.isChecked():
            # Chế độ ĐƯỜNG (Màu xanh lá)
            self.ax.plot(x_labels, y_values, color='#00ff00', marker='o', linewidth=2)
        else:
            # Chế độ CỘT (Màu xanh dương)
            self.ax.bar(x_labels, y_values, color='#3498db')
            
        # Tiêu đề và màu sắc
        self.ax.set_title(f"SẢN LƯỢNG MÁY: {machine_id}", color='#f1c40f', fontweight='bold')
        self.ax.set_ylabel("Total", color='white')

        self.ax.clear()
        
        if self.btn_chart_line.isChecked():
            self.ax.plot(x_labels, y_values, color='#00ff00', marker='o', linewidth=2)
        else:
            self.ax.bar(x_labels, y_values, color='#3498db')
            
        # ============ THÊM ĐOẠN NÀY ĐỂ HIỂN THỊ SỐ ============
        # 1. Nâng trần trục Y lên 15% để số trên đỉnh không bị lẹm vào mép trên của biểu đồ
        max_y = max(y_values) if y_values else 0
        self.ax.set_ylim(0, max_y * 1.15 if max_y > 0 else 10)
        # 2. Lặp qua các số liệu và ghi chữ lên đỉnh
        for i, val in enumerate(y_values):
            # Mẹo UX: Chỉ in số nếu > 0. 
            # (Nếu in cả số 0 thì nguyên dãy 24 giờ sẽ có 24 cái số 0 nằm lè tè dưới đất trông rất rác)
            if val > 0:
                self.ax.text(
                    i, val,                 # Tọa độ (X, Y) để đặt chữ
                    str(val),               # Nội dung chữ (ép kiểu chuỗi)
                    color='yellow',         # Chữ màu vàng cho nổi bật trên nền tối
                    ha='center',            # Căn giữa theo chiều ngang (đứng ngay giữa cột)
                    va='bottom',            # Nằm đè lên trên mép cột
                    fontweight='bold'       # In đậm
                )
        # ======================================================
        self.ax.set_title(f"SẢN LƯỢNG MÁY: {machine_id}", color='#f1c40f', fontweight='bold')
        # xoay chữu 45 độ
            
        # Ép bảng vẽ update
        self.figure.tight_layout()
        self.canvas.draw()

    def on_table_row_clicked(self, item):
        row = item.row()
        machine_id = self.tbl_production.item(row, 0).text()
        
        x_labels = []
        y_values = []
        
        # Quét 24 cột giờ (từ cột 1 đến cột 24) trên cái bảng để nhặt số liệu ra
        for col in range(1, 25): 
            hour_str = self.tbl_production.horizontalHeaderItem(col).text()
            val_str = self.tbl_production.item(row, col).text()
            
            x_labels.append(hour_str)
            y_values.append(int(val_str) if val_str.isdigit() else 0)
            
        # Bốc đủ 24 số rồi thì gọi hàm Vẽ!
        self.draw_production_chart(machine_id, x_labels, y_values)

    def eventFilter(self, a0, a1):
        """Bắt sự kiện click từ thẻ máy và mọi widget con bên trong thẻ."""
        # Dùng a1.type() và QEvent.Type.MouseButtonPress để VS Code không báo lỗi ảo
        if a1.type() == QEvent.Type.MouseButtonPress:
            machine_id = self._widget_to_machine.get(a0)
            if machine_id:
                self.open_machine_dashboard(machine_id)
                return True   # Đã xử lý, không cho event lan tiếp
        return super().eventFilter(a0, a1)

if __name__ == "__main__":
     pass