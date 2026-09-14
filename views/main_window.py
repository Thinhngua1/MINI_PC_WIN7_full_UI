import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QTreeWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self, dashboard_vm):
        super().__init__()
        # Load file UI tổng
        ui_path = os.path.join(os.path.dirname(__file__), 'main_window.ui')
        uic.loadUi(ui_path, self)

        # Lưu ViewModel
        self.dashboard_vm = dashboard_vm
        
        # Dictionary chứa các tham chiếu đến UI của từng máy để dễ dàng update (Card UI)
        self.machine_cards = {}

        # Ghi nhớ Tab đang mở mặc định để lọc UI
        self.current_line_filter = "Change Tray"

        # 1. Khởi tạo danh sách máy động
        self.setup_dynamic_machines()

        # 1.5. Cài đặt Cây Menu (Tree Menu)
        self.setup_tree_menu()

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

            # Nối tín hiệu từ LineViewModel vào Slot update của View
            line_vm.signal_update_ui.connect(lambda card=card_widget, vm=line_vm: self.update_card_ui(card, vm))

            col += 1
            if col >= max_col:
                col = 0
                row += 1

        # DỒN LAYOUT: Ép toàn bộ các thẻ dồn lên góc Trên - Bên Trái, không bị dãn khoảng cách
        self.gridLayout_machines.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        

    def setup_tree_menu(self):
        """Tạo cấu trúc nhánh cây (Style CSS đã được chuyển sang Qt Designer)"""
        
        # Xây dựng các nhánh cây bằng code (nhàn hơn kéo thả UI nhiều)
        item_line_monitor = QTreeWidgetItem(self.tree_menu, ["Line Monitor"])
        QTreeWidgetItem(item_line_monitor, ["Change Tray"])
        QTreeWidgetItem(item_line_monitor, ["Function"])
        
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

    def handle_tree_menu_click(self, item, column=0):
        """Xử lý khi user bấm vào bất kỳ thẻ nào trên cây Menu"""
        menu_name = item.text(0)
        
        # Bấm vào chữ mẹ thì tự Xổ/Thu
        if menu_name == "Line Monitor":
            item.setExpanded(not item.isExpanded())
            return
            
        page_map = {
            "Change Tray": 0,
            "Function": 0,
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

            if menu_name in ["Change Tray", "Function"]:
                print(f"[UI] Đang xem Line Monitor chế độ: {menu_name}")

                # Lưu lại Tab đang xem
                self.current_line_filter = menu_name
                # Quét toàn bộ thẻ máy đang có trên màn hình
                for machine_id, card_widget in self.machine_cards.items():
                    # Lấy dữ liệu type hiện tại của máy đó từ ViewModel

                    current_type = str(getattr(self.dashboard_vm.lines[machine_id], 'type', '') or "").strip()
                    
                    # Hiện thẻ nếu type khớp với Menu đang bấm, ngược lại thì Ẩn đi
                    if current_type == menu_name:
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
        current_type = str(getattr(line_vm, 'type', '') or "").strip()
        
        # Nếu đang đứng ở màn hình Line Monitor thì kiểm tra để Ẩn/Hiện thẻ ngay lập tức
        if getattr(self, 'current_line_filter', None) in ["Change Tray", "Function"]:
            if current_type == self.current_line_filter:
                card_widget.setVisible(True)
            else:
                card_widget.setVisible(False)

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
if __name__ == "__main__":
     pass