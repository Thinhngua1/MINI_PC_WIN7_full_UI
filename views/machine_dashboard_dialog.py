# views/machine_dashboard_dialog.py
import os
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5 import uic
from PyQt5.QtCore import Qt


class MachineDashboardDialog(QDialog):
    """
    Sub-Dashboard popup dành riêng cho từng máy.
    Nhận LineViewModel, tự connect signal, tự update khi có data mới.
    ViewModel KHÔNG biết về Dialog này (đúng chiều MVVM: VM -> View qua Signal).
    """

    def __init__(self, line_vm, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), 'machine_dashboard.ui')
        uic.loadUi(ui_path, self)

        self.line_vm = line_vm

        # Setup bảng lỗi 1 lần
        self._setup_error_table()

        # Update dữ liệu lần đầu khi mở
        self._refresh_ui()

        # Nối signal: mỗi khi LineVM có data mới → tự refresh
        self.line_vm.signal_update_ui.connect(self._refresh_ui)

        # Nút Đóng (phím ESC đã được gán trong .ui qua shortcut)
        self.btn_close_sub.clicked.connect(self.close)

    def _setup_error_table(self):
        """Cài đặt cột cho bảng lỗi. Chỉ gọi 1 lần lúc khởi tạo."""
        # Cột cuối (Thông báo) tự kéo dãn hết phần còn lại
        self.tbl_error_log.horizontalHeader().setStretchLastSection(True)
        self.tbl_error_log.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_error_log.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # Chỉ đọc, không cho edit
        self.tbl_error_log.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Ẩn số thứ tự hàng bên trái
        self.tbl_error_log.verticalHeader().setVisible(False)

        # Chọn cả hàng khi click
        self.tbl_error_log.setSelectionBehavior(QAbstractItemView.SelectRows)

    def _refresh_ui(self):
        """Hứng signal từ LineViewModel và cập nhật toàn bộ UI của Dialog."""
        vm = self.line_vm

        # ---- Helper: giây (int) → chuỗi HH:MM:SS ----
        def fmt(seconds):
            h, rem = divmod(int(seconds), 3600)
            m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        # ---- Header: Tên máy - Model - Trạng thái ----
        self.lbl_sub_machine_id.setText(
            f"{vm.machine_id}  —  {vm.machine_model}  —  {vm.status}"
        )

        # ---- Vùng Sản lượng ----
        self.lbl_sub_ok.setText(str(vm.ok_count))
        self.lbl_sub_ng.setText(str(vm.ng_count))
        self.lbl_sub_total.setText(str(vm.total_count))
        self.lbl_sub_rate.setText(f"{vm.rate}%")

        # ---- Vùng Downtime Ca Ngày ----
        self.lbl_sub_day_loss.setText(fmt(vm.day_loss_time))
        self.lbl_sub_day_error.setText(fmt(vm.day_error_time))
        self.lbl_sub_day_idle.setText(fmt(vm.day_idle_time))

        # ---- Vùng Downtime Ca Đêm ----
        self.lbl_sub_night_loss.setText(fmt(vm.night_loss_time))
        self.lbl_sub_night_error.setText(fmt(vm.night_error_time))
        self.lbl_sub_night_idle.setText(fmt(vm.night_idle_time))

        # ---- Bảng Lỗi Cảnh Báo Của Máy ----
        # error_history đã được lưu theo thứ tự mới nhất trước (insert(0,...))
        logs = vm.error_history
        self.tbl_error_log.setRowCount(len(logs))

        for row, entry in enumerate(logs):
            time_item   = QTableWidgetItem(entry.get("time", ""))
            status_item = QTableWidgetItem(entry.get("status", "ERROR"))
            msg_item    = QTableWidgetItem(entry.get("error", entry.get("message", "")))

            # Căn giữa 2 cột đầu
            time_item.setTextAlignment(Qt.AlignCenter)
            status_item.setTextAlignment(Qt.AlignCenter)

            # Tô màu theo trạng thái
            status_val = entry.get("status", "ERROR")
            if status_val == "ERROR":
                status_item.setForeground(Qt.red)
            elif status_val == "LOSS":
                status_item.setForeground(Qt.yellow)

            self.tbl_error_log.setItem(row, 0, time_item)
            self.tbl_error_log.setItem(row, 1, status_item)
            self.tbl_error_log.setItem(row, 2, msg_item)

    def closeEvent(self, event):
        """Ngắt kết nối signal khi Dialog đóng để tránh memory leak."""
        try:
            self.line_vm.signal_update_ui.disconnect(self._refresh_ui)
        except TypeError:
            pass  # Đã bị disconnect trước đó thì bỏ qua
        super().closeEvent(event)
