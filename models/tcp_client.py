import socket
import threading
import time
import struct
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal 

class TCPclientModel(QObject):

    # Tín hiệu ham rcv gui sang UI
    signal_rcv_by_server = pyqtSignal(dict)

    def __init__(self,ip:str ,port):
        super().__init__() # khởi tạo QObject
        self.ip = ip
        self.port = port

        self._status_connect = False # thêm cờ cho nút connect
        self._is_running = False # Thêm cờ này để kiểm soát vòng lặp tổng Auto-Reconnect


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
            except Exception as e: #Exception 
                print(f"[Client] loi void server ko xac dinh {e}") 
                time.sleep(1) 

    
    #B2: trao doi du lieu
    # ko cần send data trong prj này

    def receive_data(self):
        buffer = b""

        try:
            while self._status_connect:
                chunk = self.client.recv(4096)

                if not chunk:
                    print("[Client] Robot đã ngắt kết nối")
                    self._status_connect = False
                    break
                buffer += chunk

                # TCP có thể nhận thiếu hoặc nhiều packet trong một lần recv()
                while len(buffer) >= 1440:
                    packet = buffer[:1440]
                    buffer = buffer[1440:]

                    robot_mode = struct.unpack_from("<Q", packet, 24)[0]
                        # 1 ROBOT_MODE_INIT Initialized status
                        # 2 ROBOT_MODE_BRAKE_OPEN Brake switched on
                        # 3 ROBOT_MODE_POWER_STATUS Power-off status
                        # 4 ROBOT_MODE_DISABLED Disabled (no brake switched on)
                        # 5 ROBOT_MODE_ENABLE Enabled and idle (no project running, no alarm)
                        # 6 ROBOT_MODE_BACKDRIVE Drag mode
                        # 7 ROBOT_MODE_RUNNING
                        # Running status (including trajectory
                        # playback/fitting, executing motion commands,
                        # running project)
                        # 8 ROBOT_MODE_RECORDING Trajectory recording mode
                        # 9 ROBOT_MODE_ERROR
                        # There are uncleared alarms. This status has the
                        # highest priority. It returns 9 when there is an
                        # alarm, regardless of the status of the robot arm.
                        # 10 ROBOT_MODE_PAUSE Pause status
                        # 11 ROBOT_MODE_JOG Jogging status

                    # RunningStatus = struct.unpack_from("<B", packet, 1028)[0]
                    ErrorStatus = struct.unpack_from("<B", packet, 1029)[0]
                    DragStatus = struct.unpack_from("<B", packet, 1027)[0]

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    text = (
                        f"[{timestamp}] "
                        f"robot_mode={robot_mode}- ErrorStatus={ErrorStatus}"
                        f"DragStatus={DragStatus}"
                    )
                    
                    dict_raw = {"robot_mode":robot_mode, "ErrorStatus":ErrorStatus,}

                    #test Data of client    
                    # print(text)
                    
                    self.signal_rcv_by_server.emit(dict_raw)

        except (OSError, struct.error) as e:
            print(f"[Client] Lỗi nhận feedback: {e}")
            self._status_connect = False

    #B3 close
    def close(self):
        self._is_running = False # Dập cờ đang kết nối
        self._status_connect = False # Dập cờ nút connect

        self.client.close()
        print("[Client] client da dong ket noi vs server")

    

if __name__ == "__main__":
    #nhập IP nếu ko dùng UI
    # server_IP = "127.0.0.1" # hecules server
    server_IP = "192.168.1.6" 
    # server_IP = "192.168.10.101"
    Port = 30005

    # khoi tao object tu class
    my_client = TCPclientModel(server_IP,Port)

    while True:
        my_client.void_server()

