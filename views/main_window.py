from PyQt5.QtWidgets import QMainWindow
from PyQt5 import uic

class MainWindow(QMainWindow):
    def __init__(self, dashboard_vm):
        super().__init__()
        # Load file UI mà bạn sẽ kéo thả bằng Qt Designer
        # Lưu ý: Hiện tại chưa có file .ui, bạn sẽ tạo sau.
        # uic.loadUi('views/MainWindow.ui', self)
        
        self.vm = dashboard_vm
        
        # TODO: Dùng vòng lặp duyệt qua self.vm.lines để sinh ra x cái LineCardWidget
        self.setup_bindings()

    def setup_bindings(self):
        # TODO: Kết nối các signal từ ViewModel vào các hàm cập nhật UI
        pass
