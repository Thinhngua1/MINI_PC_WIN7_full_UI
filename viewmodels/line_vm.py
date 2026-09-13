from PyQt5.QtCore import QObject, pyqtSignal


class LineViewModel(QObject):
    # Tín hiệu thông báo cho View biết data đã thay đổi để vẽ lại UI
    signal_update_ui = pyqtSignal()

    def __init__(self, machine_id, machine_model):
        super().__init__()
        self.machine_id = machine_id # VD: DRB_02
        self.machine_model =  machine_model #VD: A175
        self.total_count = 0
        self.ok_count = 0
        self.ng_count = 0
        self.rate = 0.0
        self.status = "OFFLINE"

    def update_data(self, parsed_data: dict):
        # Rút số liệu từ Dictionary và gán vào bản thân ông Trưởng Line
        self.machine_model = parsed_data.get("model", "") # A175
        self.total_count = parsed_data.get("total", 0)
        self.ok_count = parsed_data.get("qtyOk", 0)       # 100
        self.ng_count = parsed_data.get("qtyNg", 0)       # 90
        self.rate = parsed_data.get("rate", 0.0)          # 90.0
        self.status = "RUNNING" # sẽ đọc sau khi team robot chỉnh
        
        # Báo cho View (Giao diện) biết tao vừa có số mới, hãy vẽ lại đi!
        self.signal_update_ui.emit()

    def set_offline(self):
        self.status = "OFFLINE"
        self.signal_update_ui.emit()
