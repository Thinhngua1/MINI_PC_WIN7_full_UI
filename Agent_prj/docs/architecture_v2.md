flowchart TD
    classDef view fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:#000
    classDef vm fill:#d5e8d4,stroke:#82b366,stroke-width:2px,color:#000
    classDef model fill:#ffe6cc,stroke:#d79b00,stroke-width:2px,color:#000
    classDef hub fill:#f8cecc,stroke:#b85450,stroke-width:3px,color:#000

    subgraph ViewLayer ["VIEW LAYER (UI - Hiển thị)"]
        UI_Main["MainWindow"]:::view
        UI_Card["LineCardWidget (x24)"]:::view
        UI_Prod["Page_Production (Bảng & Biểu đồ)"]:::view
    end

    subgraph HubLayer ["TRẠM TRUNG CHUYỂN"]
        MAIN["main.py (Wiring Hub)"]:::hub
    end

    subgraph VMLayer ["VIEWMODEL LAYER (Não bộ)"]
        DVM["DashboardViewModel\n(Quản lý QTimer, Đếm OEE)"]:::vm
        LVM["LineViewModel (x24)\n(Giữ biến run/idle/error)"]:::vm
        PVM["ProductionViewModel\n(Cắt mảng 2D, Lưu Snapshot)"]:::vm
    end

    subgraph ModelLayer ["MODEL LAYER (Data Thô)"]
        TCP["TcpServerModel\n(Đọc chuỗi CSV)"]:::model
        JSON[("Local JSON File\n(Lưu lịch sử giờ)")]:::model
    end

    %% Luồng TCP
    TCP -- "1. data_received" --> MAIN
    MAIN -- "2. raw_string" --> DVM
    DVM -- "3. Phân bổ" --> LVM
    LVM -- "4. Cập nhật thẻ máy" --> UI_Card

    %% Luồng OEE & Snapshot
    DVM == "5. signal_hourly_data\n(Mỗi 1 phút)" ==> MAIN
    MAIN == "6. Bắn Snapshot" ==> PVM
    PVM -. "7. Ghi đè" .-> JSON
    PVM == "8. signal_table_data_ready" ==> MAIN
    MAIN == "9. Đắp mảng 2D lên Bảng" ==> UI_Prod

    %% Ghi chú rủi ro
    note1>Lưu ý: Reset OK/NG lúc 08:00\nphải chạy SAU KHI chụp Snapshot]
    DVM -.- note1