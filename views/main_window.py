import os
from PyQt5.QtWidgets import QMainWindow, QWidget
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

        # 1. Khởi tạo danh sách máy động
        self.setup_dynamic_machines()

        # 2. Đấu nối các tín hiệu (Wiring Signals)
        self.wire_signals()

    def setup_dynamic_machines(self):
        """Khởi tạo giao diện động dựa trên danh sách line trong ViewModel."""
        card_ui_path = os.path.join(os.path.dirname(__file__), 'line_card.ui')
        
        row, col = 0, 0
        max_col = 3 # 3 cột như ảnh mẫu
        
        # Duyệt qua các LineViewModel đã được tạo trong DashboardViewModel
        for machine_id, line_vm in self.dashboard_vm.lines.items():
            # Load template card 
            card_widget = QWidget()
            uic.loadUi(card_ui_path, card_widget)
            
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

    def wire_signals(self):
        """Đấu nối các tín hiệu tổng của Dashboard."""
        self.dashboard_vm.signal_summary_updated.connect(self.update_summary_ui)

    def update_card_ui(self, card_widget, line_vm):
        """Hàm nhận tín hiệu và cập nhật một card máy cụ thể."""
        # Gom Tên Máy - Tên Model - Trạng Thái lên cùng 1 dòng
        card_widget.lbl_machine_id.setText(f"{line_vm.machine_id} - {line_vm.machine_model} - {line_vm.status}")
        
        card_widget.lbl_ok_count.setText(str(line_vm.ok_count))
        card_widget.lbl_ng_count.setText(str(line_vm.ng_count))
        card_widget.lbl_total_count.setText(str(line_vm.total_count))
        card_widget.lbl_rate.setText(f"{line_vm.rate}%")

        # Đổi màu vòng tròn Rate dựa trên trạng thái
        if line_vm.status == "RUNNING":
            card_widget.lbl_rate.setStyleSheet("border: 4px solid #00ff00; border-radius: 40px; background-color: transparent; color: white;")
        elif line_vm.status == "OFFLINE":
            card_widget.lbl_rate.setStyleSheet("border: 4px solid #555555; border-radius: 40px; background-color: transparent; color: white;")
        elif line_vm.status == "ALARM":
            card_widget.lbl_rate.setStyleSheet("border: 4px solid #ff3333; border-radius: 40px; background-color: transparent; color: white;")
        else:
            card_widget.lbl_rate.setStyleSheet("border: 4px solid #ffaa00; border-radius: 40px; background-color: transparent; color: white;")

    def update_summary_ui(self, summary_data):
        """Cập nhật phần Summary chung ở trên cùng."""
        self.lbl_sum_total.setText(str(summary_data['total_machine']))
        self.lbl_sum_running.setText(str(summary_data['machine_running']))
        self.lbl_sum_waiting.setText(str(summary_data['machine_WAITING']))
        self.lbl_sum_alarm.setText(str(summary_data['machine_Alarm']))
        self.lbl_sum_offline.setText(str(summary_data['machine_offline']))
        
        # Calculate overall OEE logic (mocked as simple average for now, replace with true logic if needed)
        total_ok = summary_data.get('machine_OK', 0)
        total_ng = summary_data.get('machine_NG', 0)
        overall_oee = 0.0
        # Cần logic tính OEE từ Model/ViewModel, tạm fix cứng OEE nếu chưa có data
        self.lbl_sum_oee.setText(f"{overall_oee:.1f}%")
if __name__ == "__main__":
     pass