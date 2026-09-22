from viewmodels.line_vm import LineViewModel

def test_machine_logic():
    # 1. Khởi tạo một cái thẻ máy ảo
    machine = LineViewModel("DRB_TEST", "A175")

    # 2. Hàm giả lập TCP Client bơm data và thời gian trôi
    def simulate(seconds, robot_mode, error_status, message):
        # Giả lập luồng TCP Server vừa gửi chuỗi chữ tới
        machine.message = message
        
        # Giả lập luồng TCP Client bơm Dict từ DashboardVM vào
        fake_clean_dict = {
            "robot_mode": robot_mode,
            "ErrorStatus": error_status
        }
        # Đút cục data vào chính hàm để nó tự phân tích
        machine.update_status_from_client(fake_clean_dict)
        
        print(f"\n--- NHẬN LỆNH: mode={robot_mode}, err={error_status}, msg='{message}' | TRÔI {seconds}s ---")
        for _ in range(seconds):
            machine.tick_1_second()
            print(f"Trạng thái: {machine.status:<8} | Run: {machine.run_time}s | Idle: {machine.idle_time}s | Loss: {machine.loss_time}s | Err: {machine.error_time}s")

    print("BẮT ĐẦU TEST LOGIC OEE TÍNH GIỜ...")
    simulate(3, robot_mode=7, error_status=0, message='run')
    simulate(2, robot_mode=7, error_status=0, message='wait')
    simulate(3, robot_mode=7, error_status=0, message='pause')
    
    # Bắn mã lỗi để xem nó có ưu tiên bắt Lỗi thay vì Loss không
    simulate(2, robot_mode=7, error_status=12, message='pause')
    
    # Hết lỗi (0) nhưng vẫn đang dừng cài đặt (pause) -> Kì vọng rớt về Loss
    simulate(2, robot_mode=7, error_status=0, message='pause')
    simulate(2, robot_mode=7, error_status=0, message='run')

if __name__ == "__main__":
    test_machine_logic()