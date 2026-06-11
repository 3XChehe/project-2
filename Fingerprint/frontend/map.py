import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import socket
import threading
import ast

# Cấu hình phòng
ROOM_WIDTH, ROOM_HEIGHT, ROOM_Z = 382, 420, 300 # Giả sử trần nhà cao 300cm
PYTHON_PORT = 9999
FILE_NAME = "fingerprint_3d.txt"

# Danh sách vật thể cố định: (x, y, z_start, w, h, d_height, color, label)
OBJECTS = [
    (100, 0, 0, 148, 50, 90, 'red', 'tu1'),     
    (0, 16, 0, 64, 181, 225, 'blue', 'tu2'),
    (9, 197, 0, 52, 40, 65, 'green', 'tu3'),
    (5, 265, 45, 200, 155, 5, 'orange', 'giuong'), 
    (328, 243, 0, 54, 123, 200, 'purple', 'tu5'),
    (312, 123, 0, 70, 120, 75, 'cyan', 'ban')      
]

current_pos = [0, 0, 0]
fingerprint_db = {}

# --- ĐỌC CƠ SỞ DỮ LIỆU TỪ FILE TXT ---
def load_database():
    try:
        with open(FILE_NAME, "r", encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                coord_str, rssi_str = line.split(":")
                coord = ast.literal_eval(coord_str.strip())
                rssi = ast.literal_eval(rssi_str.strip())
                fingerprint_db[coord] = rssi
        print(f"Đã nạp {len(fingerprint_db)} điểm Fingerprint vào bộ nhớ.")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {FILE_NAME}. Hãy chạy script thu thập trước!")
    except Exception as e:
        print(f"Lỗi khi đọc file: {e}")

# --- THUẬT TOÁN ĐỊNH VỊ 3D ---
def find_position_3d(current_rssi, k=3):
    distances = []
    for coord, rssi_vector in fingerprint_db.items():
        if len(rssi_vector) < 3: continue
            
        dist = np.sqrt(sum((current_rssi[i] - rssi_vector[i])**2 for i in range(3)))
        distances.append((dist, coord))
    
    if not distances:
        return current_pos[0], current_pos[1], current_pos[2]
    
    distances.sort(key=lambda x: x[0])
    neighbors = distances[:k]
    
    total_w = sum(1.0 / (d[0] + 0.1) for d in neighbors)
    
    final_x = sum(n[1][0] * (1.0 / (n[0] + 0.1)) for n in neighbors) / total_w
    final_y = sum(n[1][1] * (1.0 / (n[0] + 0.1)) for n in neighbors) / total_w
    final_z = sum(n[1][2] * (1.0 / (n[0] + 0.1)) for n in neighbors) / total_w
    
    return final_x, final_y, final_z

# --- LẮNG NGHE UDP ---
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", PYTHON_PORT))
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            rssi_str = data.decode('utf-8')
            rssi_vals = [float(x) for x in rssi_str.split(',')]
            if len(rssi_vals) >= 3:
                x, y, z = find_position_3d(rssi_vals)
                current_pos[0], current_pos[1], current_pos[2] = x, y, z
        except Exception:
            pass 

# --- HÀM VẼ KHỐI HỘP 3D ---
def draw_3d_box(ax, x, y, z, w, h, d, color, alpha=0.2):
    vertices = np.array([
        [x, y, z], [x+w, y, z], [x+w, y+h, z], [x, y+h, z],
        [x, y, z+d], [x+w, y, z+d], [x+w, y+h, z+d], [x, y+h, z+d]
    ])
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]], 
        [vertices[4], vertices[5], vertices[6], vertices[7]], 
        [vertices[0], vertices[1], vertices[5], vertices[4]], 
        [vertices[2], vertices[3], vertices[7], vertices[6]], 
        [vertices[1], vertices[2], vertices[6], vertices[5]], 
        [vertices[0], vertices[3], vertices[7], vertices[4]]  
    ]
    ax.add_collection3d(Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors='black', alpha=alpha))

# --- HIỂN THỊ ĐỒ THỊ ---
plt.ion()
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

def update_map():
    # Thiết lập góc nhìn mặc định ban đầu (chỉ chạy 1 lần duy nhất trước vòng lặp)
    ax.view_init(elev=20, azim=45)
    
    while True:
        # 1. LẤY GÓC NHÌN HIỆN TẠI (Người dùng đang xoay bằng chuột)
        # Nếu là lần chạy đầu tiên, nó sẽ lấy góc (20, 45) ở trên
        current_elev = ax.elev
        current_azim = ax.azim
        
        # 2. Xóa đồ thị cũ
        ax.clear()
        
        # Thiết lập giới hạn trục như cũ
        ax.set_xlim(0, ROOM_WIDTH)
        ax.set_ylim(0, ROOM_HEIGHT)
        ax.set_zlim(0, ROOM_Z)
        ax.set_xlabel('Trục X')
        ax.set_ylabel('Trục Y')
        ax.set_zlabel('Trục Z (Độ cao)')
        
        # Vẽ các vật thể 3D
        for x, y, z, w, h, d, color, label in OBJECTS:
            draw_3d_box(ax, x, y, z, w, h, d, color)
            ax.text(x + w/2, y + h/2, z + d + 10, label, color='black', ha='center')

        # Vẽ dữ liệu Fingerprint
        if fingerprint_db:
            fps_x, fps_y, fps_z = zip(*fingerprint_db.keys())
            ax.scatter(fps_x, fps_y, fps_z, c='gray', s=10, alpha=0.3, label='Dữ liệu mẫu')

        # Vẽ vị trí ngôi sao đỏ và hiển thị tọa độ
        ax.scatter(current_pos[0], current_pos[1], current_pos[2], c='red', s=200, marker='*', label='Tag (Thiết bị)')
        ax.text(current_pos[0], current_pos[1], current_pos[2] + 15, 
                f"({current_pos[0]:.1f}, {current_pos[1]:.1f}, {current_pos[2]:.1f})", 
                color='red', fontweight='bold', ha='center', fontsize=10)
        
        ax.set_title(f"HỆ THỐNG ĐỊNH VỊ FINGERPRINT 3D\nTọa độ Tag: X = {current_pos[0]:.1f} | Y = {current_pos[1]:.1f} | Z = {current_pos[2]:.1f}", 
                     fontsize=12, fontweight='bold', color='darkblue', pad=20)
        
        # 3. KHÔI PHỤC LẠI GÓC NHÌN MÀ NGƯỜI DÙNG VỪA XOAY
        ax.view_init(elev=current_elev, azim=current_azim)
        
        plt.draw()
        plt.pause(0.1)

# Chạy hệ thống
load_database()
threading.Thread(target=udp_listener, daemon=True).start()
update_map()