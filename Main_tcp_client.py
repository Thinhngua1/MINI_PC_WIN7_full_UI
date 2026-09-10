import socket
import threading
import time
# import file backend
from Backend.DataProcessor import DataProcessor

from PyQt5.QtCore import QObject, pyqtSignal # Thêm để chạy UI

class client(QObject):

    def __init__(self,ip:str ,port):
        super().__init__() # khởi tạo QObject
        self.ip = ip
        self.port = port

        self._status_connect = False # thêm cờ cho nút connect
        self._is_running = False # Thêm cờ này để kiểm soát vòng lặp tổng Auto-Reconnect

        # Khởi tạo cỗ máy xử lý dữ liệu(backend)
        self.processor = DataProcessor(prefix="[Client]")

    #B1: ket noi
    # create socket
    def create_socket(self):
        client_ = socket.socket(family = socket.AF_INET,type = socket.SOCK_STREAM)
        return client_

    # void serrver
    def void_server(self):
        self._is_running = True # Bật cờ cho phép chạy luồng tổng 
        # Vòng lặp Auto-Reconnect: Sẽ lặp lại liên tục nếu _is_running còn True
        while self._is_running:
            self.client = self.create_socket()

            try: 
                self.client.connect((self.ip,self.port))
                print("[Client] da ket noi thanh cong toi server")
                self._status_connect =True

                #khoi tao thread
                t_recv = threading.Thread(target = self.receive_data,daemon = True)
                t_recv.start()

                # neu nút connect đang bấm và dang kết nối
                while self._status_connect and self._is_running:
                    time.sleep(1)
                if self._is_running:
                    print("[Client] Thu ket noi lai sau 0.5 giay...\n")
                

                time.sleep(0.5)

            except ConnectionRefusedError:
                print("[Client] Loi: server chua bat hoac tu choi ket noi")
                time.sleep(1)
            except Exception: #Exception 
                print("[Client] loi void server ko xac dinh") 
                time.sleep(1) 

    
    #B2: trao doi du lieu

    def send_data(self,command):# dung vs UI

        try: # phong TH loi 

            if not self._status_connect:
                print("[Client] Chưa kết nối tới PLC, không thể gửi lệnh!")
                return
        
            mes = command + "\r\n"
            self.client.sendall(mes.encode())
            # Giữ print lệnh đã gửi cho tab TCP Client (để UI có thể thấy lệnh đã được gửi qua log vì ta chưa có text box riêng như Server)
            print(f"[Client] Sent: {command}")


        except Exception: #Exception 
            print("[Client] loi send data ko xac dinh")
            self._status_connect = False

    # Tín hiệu ham rcv gui sang UI
    signal_data_rcv = pyqtSignal(str)
    
    #receive data 
    def receive_data(self):
        
        try: # phong TH loi
            while self._status_connect:
                data_rcv = self.client.recv(1024)

                if not data_rcv:
                    print("[Client] server da chu dong ngat ket noi")
                    self._status_connect = False
                    self.close()
                    break
            
                # Bỏ dòng in data_rcv gốc vì UI đã append thông qua self.signal_data_rcv rồi
                # print("phan hoi tu server: ",data_rcv.decode())

                # Nhánh 1: Đẩy dữ liệu này lên cho UI hứng
                self.signal_data_rcv.emit(data_rcv.decode().strip())

                #nhanh 2: SQL server
                self.processor.process_and_send(data_rcv.decode().strip())


        except Exception as e: #Exception 
            #disconnect -> server send b'' -> 
            if self._status_connect == False:
                print("[Client] da nhan disconnect")
            else:
                print("[Client] loi rcv data ko xac dinh")
                self._status_connect = False

    #B3 close
    def close(self):
        self._is_running = False # Dập cờ đang kết nối
        self._status_connect = False # Dập cờ nút connect

        self.client.close()
        print("[Client] client da dong ket noi vs server")

    

if __name__ == "__main__":
    #nhập IP nếu ko dùng UI
    # server_IP = "192.168.120.42"
    # server_IP = "127.0.0.1" # hecules server
    server_IP = "192.168.10.6" 
    Port = 8500

    # khoi tao object tu class
    my_client = client(server_IP,Port)

    while True:
        my_client.void_server()

