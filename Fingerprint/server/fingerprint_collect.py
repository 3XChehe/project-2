import socket
import csv
import numpy as np

# Cấu hình
UDP_IP = "127.0.0.1"
UDP_PORT = 9999

def start_collector():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    # Thiết lập timeout ngắn để có thể dọn đệm mà không bị treo
    sock.settimeout(0.1)
    
    print(f"--- Đang lắng nghe dữ liệu từ Server C trên cổng {UDP_PORT} ---")
    print("Nhấn Ctrl+C để kết thúc.")

    with open(r'D:\project 2\radio_map_raw.csv', mode='a', newline='') as file:
        writer = csv.writer(file)

        try:
            while True:
                user_input = input("\nNhập tọa độ (x,y) và nhấn Enter để BẮT ĐẦU lấy mẫu: ")
                if not user_input: continue
                
                try:
                    target_x, target_y = user_input.split(',')
                    
                    # --- BƯỚC QUAN TRỌNG: DỌN SẠCH BỘ ĐỆM (FLUSH) ---
                    print("Đang xả bỏ dữ liệu cũ trong bộ đệm...")
                    while True:
                        try:
                            # Đọc liên tục cho đến khi không còn gói tin nào xếp hàng
                            sock.recvfrom(1024)
                        except socket.timeout:
                            # Khi không còn gì để đọc, hàm recvfrom sẽ văng timeout -> Bộ đệm đã sạch
                            break
                    
                    # --- BẮT ĐẦU LẤY DỮ LIỆU MỚI ---
                    print(f"Đang thu thập 50 mẫu MỚI NHẤT tại ({target_x}, {target_y})...")
                    samples = []
                    while len(samples) < 10:
                        try:
                            data, addr = sock.recvfrom(1024)
                            rssi_str = data.decode('utf-8')
                            rssi_vals = [float(x) for x in rssi_str.split(',')]
                            samples.append(rssi_vals)
                            
                            # Hiển thị tiến trình cho đỡ sốt ruột
                            if len(samples) % 10 == 0:
                                print(f"Đã lấy {len(samples)}/50 mẫu...")
                        except socket.timeout:
                            continue # Đợi gói tin tiếp theo từ Server C
                    
                    # Tính trung bình
                    avg_rssi = np.mean(samples, axis=0)
                    avg_rssi = np.round(avg_rssi, 2)
                    
                    # Lưu file
                    writer.writerow([target_x, target_y, avg_rssi[0], avg_rssi[1], avg_rssi[2]])
                    file.flush()
                    
                    print(f"==> THÀNH CÔNG: ({target_x}, {target_y}) -> RSSI: {avg_rssi.tolist()}")
                    
                except ValueError:
                    print("Lỗi định dạng! Vui lòng nhập x,y (Ví dụ: 382,90)")
                except Exception as e:
                    print(f"Lỗi: {e}")

        except KeyboardInterrupt:
            print("\nĐã lưu và thoát.")
        finally:
            sock.close()

if __name__ == "__main__":
    start_collector()