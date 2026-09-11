import time
import socket
import threading
from PyQt5.QtCore import QObject, pyqtSignal

class TcpServerModel(QObject):
    # cách ly bên ngoài: Các tín hiệu (Signals) phát ra cho ViewModel
    signal_data_received = pyqtSignal(str, str)  # (ip_client, chuỗi CSV thô)
    signal_connection_changed  = pyqtSignal(str, bool)    # (ip_client, status)
    # signal_data_sent = pyqtSignal(str) # prj hiện tại chưa cần 
    
    def __init__(self, port):
        super().__init__()
        self._host = "0.0.0.0"  # Lắng nghe trên tất cả network interface
        self.port = port
        self.is_running = False
        self.sock = None
        self.clients = {}  # Lưu trữ các kết nối(cả ip, port)
        self.lock = threading.Lock()
        

    def start(self):
        """Mở port và lắng nghe kết nối liên tục"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self._host, self.port))
        self.sock.listen()
        self.sock.settimeout(1.0)
        print(f"[Server] Đang lắng nghe trên port {self.port}...")

        self.is_running = True
        
        # Chạy vòng lặp chờ client trong một thread ngầm
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def _accept_loop(self):
        while self.is_running:
            try:
                if self.sock: 
                    conn, addr = self.sock.accept() #adrr =(ip, port)
                    client_id = f"{addr[0]}:{addr[1]}"
                    conn.settimeout(None) # Gỡ timeout để thread nhận không bị chết ngầm
                    print(f"[Server] Client {addr[0]} đã kết nối")
                    
                    with self.lock: # ngăn thread khác thao tác vs phần tử bất kỳ trong list clients
                        self.clients[client_id] = conn

                    self.signal_connection_changed .emit(client_id, True)
                    
                    # Mỗi client tạo 1 luồng nhận data riêng
                    #threading.Thread(target=self._recv_loop, args=(conn, client_id), daemon=True).start()
                    self._listen_thread = threading.Thread(target=self._recv_loop,args=(conn, client_id), daemon=True)
                    self._listen_thread.start()
                
            except socket.timeout:
                pass # Bình thường, kiểm tra lại cờ _status_listening
            except Exception:
                pass # Socket đã bị đóng khi stop() được gọi

    def _recv_loop(self, conn, client_id):
        """Nhận dữ liệu từ 1 client"""
        try:
            while self.is_running:
                
                data = conn.recv(1024)
                if not data: #data = b""
                    print(f"[Server] Client {client_id} đã ngắt kết nối")
                    break
                
                message = data.decode().strip()
                if message:
                    # Tuyệt đối không gọi SQL ở đây. Chỉ phát tín hiệu (Emit Signal) rồi đi nhận tiếp.
                    self.signal_data_received.emit(client_id, message)
                    print(f"CLient {client_id} đã gửi: {message}")
                    
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"[Server] Client {client_id} đã ngắt kết nối")

        except OSError as error:
            print(f"[Server] Client {client_id} mất kết nối: {error}")

        except Exception as error:
            print(f"[Server] Lỗi xử lý client {client_id}: {error}")
            
        finally:
            with self.lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            self.signal_connection_changed .emit(client_id, False)
            conn.close()

    def send(self, message: str):
        """Gửi dữ liệu tới client đang kết nối ."""
        with self.lock:
            conns = list(self.clients.values())

        if not conns:
            print("[Server] Chưa có client nào kết nối, không thể gửi!")
            return

        try:
            for conn in conns:
                conn.sendall((message + "\r\n").encode())
            
        except Exception as e:
            print(f"[Server] Lỗi gửi dữ liệu: {e}")

    def stop(self):
        self.is_running = False
        with self.lock:
            for client_id, conn in self.clients.items():
                conn.close()
            self.clients.clear()
        if self.sock:
            self.sock.close()
            self.sock = None
if __name__ == "__main__":

    server = TcpServerModel(8500)
    server.start()
       # Tạo 1 hàm test send riêng với client(ngoài project)
    # def auto_sender():
    #     counter = 1
    #     while server.is_running:
    #         time.sleep(3) # Cứ 3 giây gửi 1 lần
    #         test_msg = f"HELLO CLIENT, Message #{counter}"
    #         server.send(test_msg)
    #         print(f"--> Đã tự động gửi: {test_msg}")
    #         counter += 1
    # # Chạy hàm test ở 1 luồng phụ dưới nền
    # sender_thread = threading.Thread(target=auto_sender, daemon=True)
    # sender_thread.start()

    server._accept_thread.join()
   