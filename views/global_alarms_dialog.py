# views/global_alarms_dialog.py
import os
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5 import uic
from PyQt5.QtCore import Qt

class GlobalAlarmsDialog(QDialog):
    """
    Popup tổng hợp cảnh báo của toàn bộ các máy trong nhà máy.
    """
    def __init__(self, dashboard_vm, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), 'global_alarms.ui')
        uic.loadUi(ui_path, self)

        self.dashboard_vm = dashboard_vm

        # Cấu hình bảng
        self._setup_table()
        self._init_comboboxes()

        # Update dữ liệu ngay khi mở
        self._refresh_ui()

        # Lắng nghe thay đổi từ combobox để lọc
        self.cmb_machine.currentIndexChanged.connect(self._refresh_ui)
        self.cmb_status.currentIndexChanged.connect(self._refresh_ui)

        # Lắng nghe còi tổng từ dashboard_vm để update realtime
        self.dashboard_vm.signal_summary_updated.connect(self._refresh_ui)

        self.btn_close.clicked.connect(self.close)

    def _setup_table(self):
        header = self.tbl_global_errors.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Machine
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Code
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Số lần
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Phát sinh
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Xử lý
        
        # Cột 3 "Nội dung cảnh báo" chiếm hết phần còn lại
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setStretchLastSection(False)

        self.tbl_global_errors.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_global_errors.verticalHeader().setVisible(False)
        self.tbl_global_errors.setSelectionBehavior(QAbstractItemView.SelectRows)

    def _init_comboboxes(self):
        # Combobox Trạng thái
        self.cmb_status.addItems(["Tất cả trạng thái", "Active", "Resolved"])
        
        # Combobox Machine
        self.cmb_machine.addItem("Tất cả máy")
        # Lấy danh sách máy từ dashboard_vm
        machine_ids = sorted(list(self.dashboard_vm.lines.keys()))
        for mid in machine_ids:
            self.cmb_machine.addItem(mid)

    def _refresh_ui(self, *args):
        # Gom nhóm toàn bộ lỗi từ các máy
        aggregated_logs = {}
        
        selected_machine = self.cmb_machine.currentText()
        selected_status_filter = self.cmb_status.currentText()
        
        # Lặp qua tất cả các máy
        for machine_id, line_vm in self.dashboard_vm.lines.items():
            # Nếu có lọc máy và máy không khớp thì bỏ qua
            if selected_machine != "Tất cả máy" and machine_id != selected_machine:
                continue
                
            # Duyệt mảng lỗi của máy này
            for entry in reversed(line_vm.error_history):
                # Xác định status Active hay Resolved
                status_raw = entry.get("status", "ERROR")
                resolved = entry.get("resolved_time", "")
                status_display = "Resolved" if resolved else "Active"
                
                # Nếu có lọc trạng thái và không khớp thì bỏ qua
                if selected_status_filter != "Tất cả trạng thái" and status_display != selected_status_filter:
                    continue

                code = str(entry.get("code", 0))
                message = entry.get("message", "")
                
                key = (status_display, machine_id, code, message)
                
                if key not in aggregated_logs:
                    aggregated_logs[key] = {
                        "count": 0,
                        "last_occurred": "",
                        "last_resolved": "",
                        "raw_status": status_raw # để biết đỏ hay vàng
                    }
                
                aggregated_logs[key]["count"] += 1
                aggregated_logs[key]["last_occurred"] = entry.get("time", "")
                if resolved:
                    aggregated_logs[key]["last_resolved"] = resolved

        # Sắp xếp danh sách: cái nào mới xảy ra đưa lên đầu
        sorted_logs = sorted(aggregated_logs.items(), key=lambda x: x[1]["last_occurred"], reverse=True)
        
        self.tbl_global_errors.setRowCount(len(sorted_logs))

        for row, (key, data) in enumerate(sorted_logs):
            status_display, machine_id, code, message = key
            
            status_item   = QTableWidgetItem(status_display)
            machine_item  = QTableWidgetItem(machine_id)
            code_item     = QTableWidgetItem(code)
            msg_item      = QTableWidgetItem(message)
            count_item    = QTableWidgetItem(str(data["count"]))
            occur_item    = QTableWidgetItem(data["last_occurred"])
            resolv_item   = QTableWidgetItem(data["last_resolved"])

            # Căn giữa
            for item in [status_item, machine_item, code_item, count_item, occur_item, resolv_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Tô màu status
            if status_display == "Active":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.green)

            self.tbl_global_errors.setItem(row, 0, status_item)
            self.tbl_global_errors.setItem(row, 1, machine_item)
            self.tbl_global_errors.setItem(row, 2, code_item)
            self.tbl_global_errors.setItem(row, 3, msg_item)
            self.tbl_global_errors.setItem(row, 4, count_item)
            self.tbl_global_errors.setItem(row, 5, occur_item)
            self.tbl_global_errors.setItem(row, 6, resolv_item)
            
        self.lbl_footer.setText(f"{len(self.dashboard_vm.lines)} MACHINES ● TỔNG HỢP CẢNH BÁO")

    def closeEvent(self, a0):
        try:
            self.dashboard_vm.signal_summary_updated.disconnect(self._refresh_ui)
        except TypeError:
            pass
        super().closeEvent(a0)
