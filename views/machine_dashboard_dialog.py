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
        header = self.tbl_error_log.horizontalHeader()
        
        # Các cột ngắn: tự fit theo nội dung
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Code
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Số lần
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Phát sinh gần nhất
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Xử lý gần nhất
        
        # Cột 2 "Nội dung cảnh báo" chiếm hết phần còn lại  ← # Update
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setStretchLastSection(False)  # Tắt stretch mặc định ở cột cuối

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
        # Gom nhóm lỗi để đếm Số lần, Lần xuất hiện gần nhất và Lần xử lý gần nhất
        logs = vm.error_history
        aggregated_logs = {}
        
        # Duyệt từ cũ nhất đến mới nhất để update thời gian (last_occurred sẽ lấy cái mới nhất)
        for entry in reversed(logs):
            status = entry.get("status", "ERROR")
            code = str(entry.get("code", 0))
            message = entry.get("message", "")
            key = (status, code, message)
            
            if key not in aggregated_logs:
                aggregated_logs[key] = {
                    "count": 0,
                    "last_occurred": "",
                    "last_resolved": ""
                }
            
            aggregated_logs[key]["count"] += 1
            aggregated_logs[key]["last_occurred"] = entry.get("time", "")
            # Ưu tiên lưu thời gian xử lý của lần gần nhất
            if entry.get("resolved_time"):
                aggregated_logs[key]["last_resolved"] = entry.get("resolved_time")

        # Lấy danh sách đã gom nhóm, xếp lại theo cái nào vừa xảy ra gần nhất lên trên
        sorted_logs = sorted(aggregated_logs.items(), key=lambda x: x[1]["last_occurred"], reverse=True)
        
        self.tbl_error_log.setRowCount(len(sorted_logs))

        for row, (key, data) in enumerate(sorted_logs):
            _, code, message = key
            # Nếu đã có resolved_time → "Resolved", chưa có → "Active"  ← # Update
            status_text = "Resolved" if data["last_resolved"] else "Active"
            
            status_item   = QTableWidgetItem(status_text)
            code_item     = QTableWidgetItem(code)
            msg_item      = QTableWidgetItem(message)
            count_item    = QTableWidgetItem(str(data["count"]))
            occur_item    = QTableWidgetItem(data["last_occurred"])
            resolv_item   = QTableWidgetItem(data["last_resolved"])

            # Căn giữa các cột thông số ngắn
            for item in [status_item, code_item, count_item, occur_item, resolv_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Tô màu theo trạng thái
            if status_text == "Active":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.green)


            self.tbl_error_log.setItem(row, 0, status_item)
            self.tbl_error_log.setItem(row, 1, code_item)
            self.tbl_error_log.setItem(row, 2, msg_item)
            self.tbl_error_log.setItem(row, 3, count_item)
            self.tbl_error_log.setItem(row, 4, occur_item)
            self.tbl_error_log.setItem(row, 5, resolv_item)

    def closeEvent(self, a0):
        """Ngắt kết nối signal khi Dialog đóng để tránh memory leak."""
        try:
            self.line_vm.signal_update_ui.disconnect(self._refresh_ui)
        except TypeError:
            pass  # Đã bị disconnect trước đó thì bỏ qua
        super().closeEvent(a0)
