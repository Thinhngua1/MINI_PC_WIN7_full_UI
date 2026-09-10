import socket
import threading
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal
from Backend.DataProcessor import DataProcessor


class Server(QObject):

    # Signal gửi dữ liệu nhận được từ client lên UI → txt_log_rcv_server
    signal_data_rcv  = pyqtSignal(str)
    # Signal gửi dữ liệu đã gửi đi lên UI → txt_log_send_server
    signal_data_sent = pyqtSignal(str)
    

    def __init__(self, port: int):
        super().__init__()  # Bắt buộc khi kế thừa QObject
        self._host = "0.0.0.0"  # Lắng nghe trên tất cả network interface
        self._port = port
        self._status_listening = False
        self._sock: Optional[socket.socket] = None #optional giúp khai báo kiểu dữ liệu, cho pyalance biết _sock có thể là socket.socket hoặc none 

        # Lưu conn client hiện tại (nhiều client tại 1 thời điểm)
        self._connections: list[socket.socket] = []
        self._lock = threading.Lock()

        # Khởi tạo cỗ máy xử lý dữ liệu (truyền prefix để log đi đúng tab)
        self.processor = DataProcessor(prefix="[Server]")

    def open(self):
        """Bind socket và bắt đầu vòng lặp accept trong thread ngầm."""
        self._sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # tránh lỗi "Address already in use"
        address = (self._host, self._port)
        self._sock.bind(address)
        self._sock.listen()
        self._sock.settimeout(1.0)  # Timeout 1s để vòng lặp accept có thể kiểm tra cờ dừng

        print(f"[Server] Đang lắng nghe trên port {self._port}...")
        self._status_listening = True

        self._listen_thread = threading.Thread(target=self._loop_listen, daemon=True)
        self._listen_thread.start()

    def _loop_listen(self):
        """Vòng lặp chờ client kết nối (chạy trong thread ngầm)."""
        while self._status_listening:
            if self._sock is None:
                break
            try:
                conn, addr = self._sock.accept()
                conn.settimeout(None)  # Gỡ timeout để thread nhận không bị chết ngầm
                print(f"[Server] Client {addr} đã kết nối")

                # Lưu conn client mới nhất
                with self._lock:
                    self._connections.append(conn)

                # Mỗi client được phục vụ bởi 1 thread nhận riêng
                t_recv = threading.Thread(
                    target=self._receive, args=(conn, addr), daemon=True
                )
                t_recv.start()

            except socket.timeout:
                pass  # Bình thường, kiểm tra lại cờ _status_listening
            except Exception:
                pass  # Socket đã bị đóng khi stop() được gọi

    def _receive(self, conn: socket.socket, addr):
        """Nhận dữ liệu từ client và emit signal lên UI."""
        try:
            while self._status_listening:
                data = conn.recv(1024)
                if not data:
                    print(f"[Server] Client {addr} đã ngắt kết nối")
                    break

                message = data.decode().strip()

                # Nhánh 1: Đẩy lên ô "Received data" trên tab Server (không qua stdout)
                self.signal_data_rcv.emit(message)

                # Nhánh 2: Xử lý và đẩy lên SQL (giống TCP Client) -> nhận data từ SQL, emit tín hiệu lên Client, UI
                sql_response  = self.processor.process_and_send(message)

                if sql_response:
                    conn.sendall((sql_response + "\r\n").encode())
                    self.signal_data_rcv.emit(sql_response) # Chỉ emit 1 lần

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            print(f"[Server] Client {addr} đã ngắt kết nối")

        except OSError as error:
            print(f"[Server] Client {addr} mất kết nối: {error}")

        except Exception as error:
            print(f"[Server] Lỗi xử lý client {addr}: {error}")


        finally: # dọn dẹp khi hàm _receive() kết thúc
            with self._lock: #Khóa để tránh xung đột giữa các thread khi truy cập các conn.
                if conn in self._connections:
                    self._connections.remove(conn)
            conn.close()

    def send(self, message: str):
        """Gửi dữ liệu tới client đang kết nối (gọi từ UI)."""
        with self._lock:
            conns = list(self._connections)

        if not conns:
            print("[Server] Chưa có client nào kết nối, không thể gửi!")
            return

        try:
            for conn in conns:
                conn.sendall((message + "\r\n").encode())
            
                # Đẩy lên ô "Sent data" trên tab Server 
                self.signal_data_sent.emit(message)

        except Exception as e:
            print(f"[Server] Lỗi gửi dữ liệu: {e}")

    def stop(self):
        """Dừng server: tắt cờ, đóng socket, chờ thread kết thúc."""
        self._status_listening = False

        # Đóng conn client hiện tại (nếu có)
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception:
                    pass
            self._connections.clear()

        # Đóng listening socket → unblock accept() ngay lập tức
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

        print("[Server] Đã dừng lắng nghe")


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    server = Server(8000)
    server.open()
    server._listen_thread.join()