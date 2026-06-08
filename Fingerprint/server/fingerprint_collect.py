import socket
import numpy as np

# Cấu hình
UDP_IP = "127.0.0.1"
UDP_PORT = 9999
FILE_NAME = "fingerprint_3d.txt"

def start_collector():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.1)
    
    print(f"--- Đang lắng nghe Server C trên cổng {UDP_PORT} ---")
    print(f"Dữ liệu sẽ được lưu vào file: {FILE_NAME}")
    
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
                
                # Lấy 10 mẫu mới
                print(f"Đang thu thập 10 mẫu tại ({target_x}, {target_y}, {target_z})...")
                samples = []
                sock.settimeout(10.0) # Tăng timeout khi đang lấy mẫu
                
                while len(samples) < 10:
                    try:
                        data, addr = sock.recvfrom(1024)
                        rssi_str = data.decode('utf-8')
                        rssi_vals = [float(x) for x in rssi_str.split(',')]
                        
                        if len(rssi_vals) >= 3:
                            samples.append(rssi_vals[:3])
                            if len(samples) % 10 == 0:
                                print(f"Đã lấy {len(samples)}/50 mẫu...")
                    except socket.timeout:
                        print("Cảnh báo: Mất kết nối với Server C!")
                        break
                
                if len(samples) == 10:
                    # Tính trung bình
                    avg_rssi = np.round(np.mean(samples, axis=0), 2).tolist()
                    
                    # Tạo chuỗi theo định dạng yêu cầu
                    # VD: (382.0, 90.0, 150.0) : [-72.37, -64.25, -74.87]
                    line = f"({target_x}, {target_y}, {target_z}) : {avg_rssi}\n"
                    
                    file.write(line)
                    file.flush()
                    print(f"==> Đã lưu: {line.strip()}")
                
            except ValueError:
                print("Lỗi định dạng số!")
            except KeyboardInterrupt:
                print("\nĐã thoát chương trình.")
                break
    sock.close()

if __name__ == "__main__":
    start_collector()