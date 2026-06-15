import socket
import numpy as np

# Cấu hình
UDP_IP = "127.0.0.1"
UDP_PORT = 9999
FILE_NAME = "fingerprint_3d.txt"

def normalize_rssi(rssi_vals):

    v = np.array(rssi_vals, dtype=float)

    mean = np.mean(v)

    return (v - mean).tolist()

def start_collector():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.1)
    
    print(f"--- Đang lắng nghe Server C trên cổng {UDP_PORT} ---")
    print(f"Dữ liệu CHUẨN HÓA sẽ được lưu vào file: {FILE_NAME}")
    
    with open(FILE_NAME, mode='a', encoding='utf-8') as file:
        while True:
            try:
                user_input = input("\nNhập tọa độ x,y,z (VD: 382,90,150) hoặc Ctrl+C để thoát: ")
                if not user_input: continue
                
                parts = user_input.split(',')
                if len(parts) != 3:
                    print("Lỗi: Vui lòng nhập đúng 3 giá trị x,y,z cách nhau bằng dấu phẩy.")
                    continue
                
                target_x, target_y, target_z = map(float, parts)
                sock.settimeout(0.1)
                
                # Xả bộ đệm (xóa dữ liệu cũ)
                print("Đang xả bộ đệm...")
                while True:
                    try:
                        sock.recvfrom(1024)
                    except socket.timeout:
                        break
                
                # Lấy 20 mẫu mới
                print(f"Đang thu thập 20 mẫu RSSI tại ({target_x}, {target_y}, {target_z})...")
                samples = []
                sock.settimeout(10.0) 
                
                while len(samples) < 50:
                    try:
                        data, addr = sock.recvfrom(1024)
                        rssi_str = data.decode('utf-8')
                        rssi_vals = [float(x) for x in rssi_str.split(',')]
                        
                        if len(rssi_vals) >= 3:
                            samples.append(rssi_vals[:3])
                            if len(samples) % 10 == 0:
                                print(f"Đã lấy {len(samples)}/20 mẫu...")
                    except socket.timeout:
                        print("Cảnh báo: Mất kết nối với Server C!")
                        break
                
                if len(samples) == 50:
                    # 1. Tính trung bình RSSI thô từ 20 mẫu
                    avg_raw_rssi = np.mean(samples, axis=0)

                    normalized_rssi = normalize_rssi(avg_raw_rssi)

                    normalized_rssi = [
                        round(x, 4)
                        for x in normalized_rssi
                    ]

                    line = (
                        f"({target_x}, {target_y}, {target_z}) : "
                        f"{[round(x,2) for x in avg_raw_rssi]} : "
                        f"{normalized_rssi}\n"
                    )
                    
                    file.write(line)
                    file.flush()
                    print(f"==> Đã lưu (Đã chuẩn hóa): {line.strip()}")
                
            except ValueError:
                print("Lỗi định dạng số!")
            except KeyboardInterrupt:
                print("\nĐã thoát chương trình.")
                break
    sock.close()

if __name__ == "__main__":
    start_collector()