# Factory Monitor Dashboard - Architecture v2

Dưới đây là sơ đồ kiến trúc MVVM tổng thể của ứng dụng, được cập nhật sau quá trình tích hợp module Production, Biểu đồ và xử lý dữ liệu Realtime.

```mermaid
flowchart TD
    %% Định nghĩa màu sắc giống hệt file Draw.io cũ
    classDef view fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:#000
    classDef vm fill:#d5e8d4,stroke:#82b366,stroke-width:2px,color:#000
    classDef model fill:#f8cecc,stroke:#b85450,stroke-width:2px,color:#000
    classDef ext fill:#e1d5e7,stroke:#9673a6,stroke-width:2px,color:#000
    classDef note fill:#fff2cc,stroke:#d6b656,stroke-width:1px,stroke-dasharray: 5 5

    %% ================= VIEW LAYER =================
    subgraph VIEW ["VIEW Layer (UI Components)"]
        v1["MainWindow_UI\n(Main Shell)"]:::view
        v2["QTreeWidget\n(Sidebar Menu)"]:::view
        v3["Header\n(Time, Shift, Status)"]:::view
        v4["Line Cards\n(Grid of Widgets)"]:::view
        
        %% [MỚI] Giao diện trang Production
        v5["Production Page\n- QTableWidget (24h)\n- Matplotlib Chart\n- ĐƯỜNG/CỘT Toggle"]:::view

        v1 --- v2
        v1 --- v3
        v1 --- v4
        v1 --- v5
    end

    %% ================= VIEWMODEL LAYER =================
    subgraph VIEWMODEL ["VIEWMODEL Layer (Presentation Logic)"]
        vm1["DashboardViewModel\n(Orchestrator)\n- 1-Minute Timer\n- signal_hourly_data"]:::vm
        
        %% [MỚI] Đếm giờ Idle/Error/Run
        vm2["LineViewModel\n- tick_1_second()\n- Status/Count/Rate"]:::vm
        
        vm3["SummaryViewModel\n(Aggregated Data)"]:::vm
        
        %% [MỚI] Kẻ nhai data + Xử lý phép trừ Delta
        vm4["ProductionViewModel\n- save_hourly_snapshot()\n- Xử lý toán học: (Giờ sau - Giờ trước)\n- signal_table_data_ready"]:::vm
        
        vm1 -- "owns N" --> vm2
        vm1 -- "owns 1" --> vm3
    end

    %% ================= MODEL LAYER =================
    subgraph MODEL ["MODEL Layer (Data + Services)"]
        m1["TcpServerService\n- signal_data_received"]:::model
        m2["DataProcessorService\n- Parse CSV\n- Save JSON logs"]:::model
        m3["ConfigManager\n(Singleton)"]:::model
        m4["ShiftManager"]:::model
    end

    %% ================= EXTERNAL SYSTEMS =================
    subgraph EXT ["External Systems"]
        e1{{"Dobot Robotic Arms\n(TCP Clients)"}}:::ext
        e2{{"SQL Server REST API"}}:::ext
        e3{{"JSON Log Files\n(Raw Data)"}}:::ext
        
        %% [MỚI] File lưu Snapshot
        e4{{"Production JSON\n(Hourly Snapshots)"}}:::ext
    end

    %% ================= WIRING HUB =================
    WIRING>"main.py (Wiring Hub)\nTrạm đấu dây tập trung\n(Không cho phép View và Model tự gọi nhau)"]:::note
    WIRING -.- vm1
    WIRING -.- v1
    WIRING -.- vm4

    %% ================= KẾT NỐI (CONNECTIONS) =================
    
    %% Nét đứt màu Cam (Data Binding / Signals)
    m2 -. "signal_line_data_updated" .-> vm1
    vm1 -. "signal_time" .-> v3
    vm1 -. "signal_summary_updated" .-> v1
    vm2 -. "signal_update_ui" .-> v4
    
    %% [MỚI] Giao tiếp Realtime & Snapshot
    vm1 -. "signal_hourly_data\n(Mỗi 1 Phút)" .-> vm4
    vm4 -. "signal_table_data_ready\n(Mảng 2 chiều 24h)" .-> v5

    %% Nét liền màu Xanh (Commands / Method Calls)
    v5 -- "btn_load_data.clicked" --> vm4
    v2 -- "handle_tree_menu_click\n(Lọc ẩn/hiện thẻ máy)" --> v4

    %% Nét liền màu Đỏ (Internal Data Flow)
    m1 == "Raw TCP Data" ==> m2
    m2 -. "Reads Config" .-> m3

    %% Nét liền đậm màu Tím (External System)
    e1 == "TCP Socket" ==> m1
    m2 == "HTTP POST" ==> e2
    m2 -. "JSON Lines" .-> e3
    vm4 -. "Save/Load JSON" .-> e4

```

## Ghi chú các Mũi tên (Legend)
- **Nét đứt (-.->)**: Data Binding (Signal/Slot) - Dữ liệu truyền từ dưới lên trên.
- **Nét liền mỏng (--->)**: Commands - Lệnh điều khiển từ trên xuống dưới.
- **Nét liền kép (===>)**: External / Internal Data Flow - Luồng dữ liệu hệ thống vật lý.
- **Box Màu vàng nhạt**: Các File/Class không thuộc Layer cụ thể nhưng đóng vai trò quản lý chéo (Ví dụ: `main.py`).

## Các phần đã bổ sung so với v1:
1. Thêm cụm **Production Page (v5)** và **ProductionViewModel (vm4)**.
2. Thể hiện cơ chế 1-Minute Timer và phép trừ Data (`Giờ sau - Giờ trước`).
3. Làm rõ luồng truyền Mảng 2 chiều (`table_rows`) thẳng từ ViewModel sang View để bảo vệ kiến trúc MVVM.
4. Thêm node quản lý file JSON Production riêng biệt.
5. Thể hiện trạm đấu dây `main.py` ở trung tâm.
