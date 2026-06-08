# BLE Indoor Positioning System
## Hướng dẫn cài đặt và chạy

---

## Kiến trúc hệ thống

```
ESP32 Scanner 1 ─┐
ESP32 Scanner 2 ─┼──(TCP 8888)──► server.c ──(UDP 9999)──► main.py (Python Frontend)
ESP32 Scanner 3 ─┘                    ▲
                                      │ (UDP 8889 – lệnh mode)
                                  main.py
```

### Luồng dữ liệu
| Chế độ | Server C gửi | Python nhận |
|--------|-------------|-------------|
| Trilateration | `TRIL:d1,d2,d3` (cm) | Vẽ bản đồ 2D + tam giác |
| Fingerprint | `FING:r1,r2,r3` (RSSI) | Collector lưu file / kNN định vị 3D |

---

## Cấu trúc thư mục

```
project/
├── server/
│   └── server.c          ← Server C (Windows / Linux)
├── frontend/
│   └── main.py           ← Python frontend
└── fingerprint_3d.txt    ← Database fingerprint (tự sinh khi collect)
```

---

## 1. Build Server C

### Windows (MinGW / MSYS2)
```bash
cd server
gcc server.c -o server.exe -lws2_32 -lm
server.exe
```

### Linux / WSL
```bash
cd server
gcc server.c -o server -lm
./server
```

> Server lắng nghe:
> - **TCP 8888** – nhận RSSI từ các ESP32 Scanner
> - **UDP 9999** – gửi dữ liệu tới Python
> - **UDP 8889** – nhận lệnh mode từ Python

---

## 2. Chạy Python Frontend

```bash
pip install matplotlib numpy
cd frontend
python main.py
```

### Menu:
```
═══════════════════════════════════════
  MENU CHÍNH
═══════════════════════════════════════
  1. Trilateration (định vị 2D)
  2. Fingerprinting (định vị 3D / thu mẫu)
  3. Thoát
```

Chọn **2 → Fingerprinting**:
```
  FINGERPRINTING
────────────────────────────────────────
  1. Thu thập mẫu (Fingerprint Collector)
  2. Định vị (kNN Localization)
  3. Quay lại menu chính
```

---

## 3. Cấu hình Scanner (server.c)

Chỉnh MAC + tham số cho đúng phần cứng thực tế:

```c
static Scanner scanners[3] = {
    {"c8:f0:9e:26:48:80", -52.55f, 1.85f, ...},  // Scanner 1
    {"d4:e9:f4:b1:69:a0", -61.26f, 1.60f, ...},  // Scanner 2
    {"b0:cb:d8:9a:64:40", -51.25f, 4.30f, ...},  // Scanner 3
};
```

| Field | Ý nghĩa |
|-------|---------|
| `mac` | MAC của ESP32 Scanner |
| `rssi0` | RSSI đo được tại 1m (calibrate) |
| `n` | Hệ số suy hao môi trường |

---

## 4. Cấu hình tọa độ Scanner (main.py)

Chỉnh vị trí vật lý của 3 scanner trong phòng (đơn vị cm):

```python
S1 = np.array([250, 420])   # góc xa
S2 = np.array([230, 0])     # góc gần cửa
S3 = np.array([0, 190])     # góc trái
```

---

## 5. Quy trình thu thập Fingerprint

1. Chạy Server C và Python frontend
2. Chọn **2 → 1 (Collector)**
3. Đặt thiết bị (beacon) tại điểm cần đo
4. Nhập tọa độ x,y,z (cm), ví dụ: `200,300,100`
5. Chương trình tự thu 50 mẫu → tính trung bình → lưu vào `fingerprint_3d.txt`
6. Lặp lại với các điểm khác (phủ đều phòng)
7. Khi đủ dữ liệu → chọn **2 → 2 (Định vị)**

---

## 6. Thứ tự khởi động

```
1. server.exe  (hoặc ./server)
2. python main.py
3. Bật các ESP32 Scanner (tự kết nối TCP)
4. Bật ESP32 Beacon (phát BLE)
```

---

## Ghi chú
- Nhấn **Ctrl+C** trong cửa sổ Python để quay về menu
- File `fingerprint_3d.txt` được append mỗi lần collect, xóa thủ công nếu muốn reset
- Cửa sổ đồ thị Matplotlib cập nhật real-time ~10–20 fps
