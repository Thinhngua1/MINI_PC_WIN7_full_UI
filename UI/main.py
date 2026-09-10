import os
import sys
import threading
import time
import json
from datetime import datetime


# from backend_tcp import TcpClient
dir_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(dir_path)

sys.path.insert(0, parent_path) # add path cua Main_tcp_client.py
from Main_tcp_client import client
from Main_TCP_server import Server

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from MainWindow_UI import Ui_MainWindow

# AI: đưa tất cả print lên log
# --- LỚP HỖ TRỢ CHUYỂN HƯỚNG CONSOLE LOG (route tĩnh theo prefix) ---
class StreamToPlainTextEdit(QtCore.QObject):
    sig_write = QtCore.pyqtSignal(str)

    def __init__(self, client_log, server_rcv_log,server_send_log, original_stream):
        """
        client_log : Ô log của TCP Client
        server_log : Ô log của TCP Server
        """
        super().__init__()
        self.client_log    = client_log
        self.server_rcv_log    = server_rcv_log
        self.server_send_log    = server_send_log
        self.original_stream = original_stream
        self.sig_write.connect(self._write)

        # Khóa an toàn khi có nhiều luồng cùng gọi print
        self.lock = threading.Lock()

    def write(self, text):
        # 1. Vẫn in ra console đen (nếu có)
        if self.original_stream is not None:
            self.original_stream.write(text)

        clean_text = text.strip()
        if clean_text:
            # 2. Đẩy sang UI — _write chạy trên luồng chính qua signal
            self.sig_write.emit(clean_text)

    def flush(self):
        pass

    def _write(self, text):
        # Route thông minh: Nếu log có chữ [Server] thì ném vào tab Server, ngược lại ném vào tab Client
        if "[Server]" in text:
            
            if "[Server] [DataProcessor]" in text:
                self.server_send_log.appendPlainText(text)
            else:
                self.server_rcv_log.appendPlainText(text)

        else:
            if self.client_log:
                self.client_log.appendPlainText(text)

#---------------------------------------------------------


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ===================================================
        # TAB TCP CLIENT — widgets()
        # ===================================================
        self.btn_connect = self.ui.btn_connect
        self.txt_IP      = self.ui.txt_IP
        self.txt_port    = self.ui.txt_port
        self.txt_send    = self.ui.txt_send
        self.btn_send    = self.ui.btn_send

        # ===================================================
        # TAB TCP SERVER — widgets
        # ===================================================
        self.btn_listen          = self.ui.btn_listen
        self.txt_port_server     = self.ui.txt_port_server
        self.btn_send_2          = self.ui.btn_send_2
        self.txt_send_2          = self.ui.txt_send_2
        self.txt_log_rcv_server  = self.ui.txt_log_rcv_server
        self.txt_log_send_server = self.ui.txt_log_send_server

    # ---------------------------------------------------------
        # KẾT NỐI TÍN HIỆU (SIGNAL) VỚI HÀM XỬ LÝ (SLOT)
        # ---------------------------------------------------------
        # TCP CLIENT
        self.btn_connect.clicked.connect(self.connect_to_server)
        self.btn_send.clicked.connect(self.send_data_to_server)

        # TCP SERVER
        self.btn_listen.clicked.connect(self.toggle_listen)
        self.btn_send_2.clicked.connect(self.send_from_server)

    # AI: route print() tới đúng log dựa vào prefix [Server]
        self._stdout_redirector = StreamToPlainTextEdit(
            self.ui.txt_log,             # TCP Client log
            self.ui.txt_log_rcv_server,
            self.ui.txt_log_send_server,
            sys.stdout
        )
        sys.stdout = self._stdout_redirector


    # ==========================================================
    # PHẦN TCP CLIENT
    # ==========================================================

    def connect_to_server(self):
        """Nút Connect/Disconnect tab TCP Client (công tắc 2 chiều)."""
        trang_thai_nut = self.btn_connect.text()

        if trang_thai_nut == "CONNECT":
            ip_val   = self.txt_IP.text().strip()
            port_val = self.txt_port.text().strip()
            
            if not ip_val or not port_val:
                print("Vui lòng nhập đầy đủ IP và Port!")
                return
                
            try:
                port_int = int(port_val)
                
                # 1. Khởi tạo Backend
                self.my_tcp_backend = client(ip_val, port_int)
                
                # 2. Bật luồng chạy ngầm
                backend_thread = threading.Thread(
                    target=self.my_tcp_backend.void_server, daemon=True
                )
                backend_thread.start()
                print(f"Đang kết nối tới {ip_val}:{port_int}")
                
                # 3. Cập nhật giao diện
                time.sleep(1)  # Chờ _status_connect cập nhật
                if self.my_tcp_backend._status_connect:
                    self.btn_connect.setText("DISCONNECT")
                    self.btn_connect.setStyleSheet("background-color: red; color: white;")
                
            except ValueError:
                print("Port bắt buộc phải là số nguyên!")

        else:
            # Ngắt kết nối
            if hasattr(self, 'my_tcp_backend'):
                self.my_tcp_backend.close()

            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("background-color: green; color: white;")

    def send_data_to_server(self):
        """Gửi lệnh từ tab TCP Client."""
        cmd = self.txt_send.text().strip()
        self.my_tcp_backend.send_data(cmd)

    # Hứng signal từ class client
    def update_log_ui(self, mes):
        self.ui.txt_log.appendPlainText(f"{mes}")


    # ==========================================================
    # PHẦN TCP SERVER
    # ==========================================================

    def toggle_listen(self):
        """Nút LISTEN/CLOSE — bật hoặc tắt TCP Server (công tắc 2 chiều)."""
        trang_thai_nut = self.btn_listen.text()

        if trang_thai_nut == "LISTEN":
            # =========================================
            # CHẾ ĐỘ 1: BẮT ĐẦU LẮNG NGHE
            # =========================================
            port_val = int(self.txt_port_server.text().strip())

            if not port_val:
                print("[Server] Vui lòng nhập Port!")
                return

            try:
                
                # 1. Khởi tạo backend Server
                self.my_tcp_server = Server(port_val)

                # 2. Kết nối signal nhận data → txt_log_rcv_server
                self.my_tcp_server.signal_data_rcv.connect(self._on_server_data_received)

                # 2b. Kết nối signal data đã gửi → txt_log_send_server
                self.my_tcp_server.signal_data_sent.connect(self._on_server_data_sent)

                # 3. Bật server (bind + listen + thread)
                self.my_tcp_server.open()

                # 4. Bật hiệu ứng đỏ ( giống Hercules)
                self.btn_listen.setText("CLOSE")
                self.btn_listen.setStyleSheet("background-color: red; color: white;")

                

            except ValueError:
                print("[Server] Port bắt buộc phải là số nguyên!")
            except OSError as e:
                print(f"[Server] Lỗi bind socket: {e}")

        else:
            # =========================================
            # CHẾ ĐỘ 2: DỪNG LẮNG NGHE
            # =========================================

            # Trả nút về trạng thái ban đầu (xanh - LISTEN)
            self.btn_listen.setText("LISTEN")
            self.btn_listen.setStyleSheet("background-color: green; color: white;")
            self.my_tcp_server.stop()

    def _on_server_data_received(self, message: str):
        """Hứng signal data nhận được → txt_log_rcv_server."""
        self.txt_log_rcv_server.appendPlainText(message)

    def _on_server_data_sent(self, message: str):
        """Hứng signal data đã gửi đi → txt_log_send_server."""
        self.txt_log_send_server.appendPlainText(message)

    def send_from_server(self):
        """Gửi dữ liệu từ Server tới client đang kết nối."""
        if not hasattr(self, 'my_tcp_server') or not self.my_tcp_server._status_listening:
            print("[Server] Server chưa bật, không thể gửi!")
            return

        cmd = self.txt_send_2.text().strip()
        

        # dobot gửi data + emit signal_data_sent → _on_server_data_sent → txt_log_send_server
        self.my_tcp_server.send(cmd)
        self.txt_send_2.clear()

        # # SQL gửi data + emit signal_data_sent → _on_server_data_sent → txt_log_send_server
        # data_SQL = self.my_tcp_server.processor.data_rcv_SQL
        # self.my_tcp_server.send(data_SQL)

        # if not data_SQL:
        #     print("[Server] Chưa có phản hồi từ SQL")
        #     return
    # ==========================================================
    # ĐÓNG APP
    # ==========================================================

    def closeEvent(self, a0):
        # Khôi phục luồng print bình thường khi tắt app
        sys.stdout = sys.__stdout__

        # Dừng TCP Client (nếu đang kết nối)
        if hasattr(self, 'my_tcp_backend'):
            self.my_tcp_backend.close()

        # Dừng TCP Server (nếu đang listen)
        if hasattr(self, 'my_tcp_server'):
            self.my_tcp_server.stop()

        a0.accept()


if __name__ == "__main__":
    # Khởi tạo Application (bắt buộc phải có trong PyQt5)
    app = QtWidgets.QApplication(sys.argv)
    
    # Tạo đối tượng cửa sổ chính từ Class của bạn
    main_window = MainWindow()
    
    # Lệnh hiển thị cửa sổ lên màn hình
    main_window.show()
    
    # Giữ cho chương trình giao diện chạy vòng lặp vô tận (giống while True)
    sys.exit(app.exec_())

# Luồng hàm rcv (server):
# Dobot gửi data → Thread _receive ngầm nhận được →
# Gọi signal_data_rcv.emit(data) → Signal truyền thẳng về _on_server_data_received trên luồng UI →
# txt_log_rcv_server tự động in ra màn hình.