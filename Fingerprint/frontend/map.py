import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import socket
import threading
import ast

# Cấu hình phòng
ROOM_WIDTH, ROOM_HEIGHT, ROOM_Z = 382, 420, 300 
PYTHON_PORT = 9999
FILE_NAME = "fingerprint_3d.txt"

OBJECTS = [
    (100, 0, 0, 148, 50, 90, 'red', 'tu1'),     
    (0, 16, 0, 64, 181, 225, 'blue', 'tu2'),
    (9, 197, 0, 52, 40, 65, 'green', 'tu3'),
    (5, 265, 45, 200, 155, 5, 'orange', 'giuong'), 
    (328, 243, 0, 54, 123, 200, 'purple', 'tu5'),
    (312, 123, 0, 70, 120, 75, 'cyan', 'ban')      
]

current_pos = [0.0, 0.0, 0.0]
fingerprint_db = []

def normalize_rssi(rssi_vals):

    v = np.array(rssi_vals, dtype=float)

    mean = np.mean(v)

    return v - mean

# --- ĐỌC CƠ SỞ DỮ LIỆU TỪ FILE TXT ---
def load_database():
    try:
        with open(FILE_NAME, "r", encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                coord_str, rssi_str = line.split(":")
                coord = ast.literal_eval(coord_str.strip())
                rssi = ast.literal_eval(rssi_str.strip())
                fingerprint_db.append(
                    (
                        coord,
                        np.array(rssi, dtype=float)
                    )
                )
        print(f"Đã nạp {len(fingerprint_db)} điểm Fingerprint ĐÃ CHUẨN HÓA vào bộ nhớ.")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {FILE_NAME}. Hãy chạy script thu thập trước!")
    except Exception as e:
        print(f"Lỗi khi đọc file: {e}")

# --- THUẬT TOÁN ĐỊNH VỊ 3D CHUẨN HÓA VECTOR ---
def find_position_3d(current_raw_rssi):

    if len(fingerprint_db) == 0:
        return current_pos[0], current_pos[1], current_pos[2]

    current_vec = normalize_rssi(
        current_raw_rssi
    )

    distances = []

    for coord, db_vec in fingerprint_db:

        dist = np.linalg.norm(
            current_vec - db_vec
        )

        distances.append(
            (
                dist,
                coord
            )
        )

    distances.sort(
        key=lambda x: x[0]
    )

    K = min(
        10,
        len(distances)
    )

    neighbors = distances[:K]

    sigma = neighbors[-1][0]

    if sigma < 0.0001:
        sigma = 0.0001

    weights = []

    for dist, _ in neighbors:

        w = np.exp(
            -(dist * dist)
            /
            (2 * sigma * sigma)
        )

        weights.append(w)

    total_w = sum(weights)

    x = sum(
        neighbors[i][1][0]
        *
        weights[i]
        for i in range(K)
    ) / total_w

    y = sum(
        neighbors[i][1][1]
        *
        weights[i]
        for i in range(K)
    ) / total_w

    z = sum(
        neighbors[i][1][2]
        *
        weights[i]
        for i in range(K)
    ) / total_w

    return x, y, z
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
    ax.view_init(elev=20, azim=45)
    
    while True:
        current_elev = ax.elev
        current_azim = ax.azim
        
        ax.clear()
        ax.set_xlim(0, ROOM_WIDTH)
        ax.set_ylim(0, ROOM_HEIGHT)
        ax.set_zlim(0, ROOM_Z)
        ax.set_xlabel('Trục X')
        ax.set_ylabel('Trục Y')
        ax.set_zlabel('Trục Z (Độ cao)')
        
        for x, y, z, w, h, d, color, label in OBJECTS:
            draw_3d_box(ax, x, y, z, w, h, d, color)
            ax.text(x + w/2, y + h/2, z + d + 10, label, color='black', ha='center')

        if fingerprint_db:
            coords = [fp[0] for fp in fingerprint_db]

            fps_x = [c[0] for c in coords]
            fps_y = [c[1] for c in coords]
            fps_z = [c[2] for c in coords]
            ax.scatter(fps_x, fps_y, fps_z, c='gray', s=15, alpha=0.4, label='Dữ liệu mẫu')

        # Vẽ vị trí đối tượng di chuyển
        ax.scatter(current_pos[0], current_pos[1], current_pos[2], c='red', s=200, marker='*', label='Tag (Thiết bị)')
        ax.text(current_pos[0], current_pos[1], current_pos[2] + 15, 
                f"({current_pos[0]:.1f}, {current_pos[1]:.1f}, {current_pos[2]:.1f})", 
                color='red', fontweight='bold', ha='center', fontsize=10)
        
        ax.set_title(f"HỆ THỐNG ĐỊNH VỊ FINGERPRINT VỚI VECTOR CHUẨN HÓA\nTọa độ Tag: X = {current_pos[0]:.1f} | Y = {current_pos[1]:.1f} | Z = {current_pos[2]:.1f}", 
                     fontsize=12, fontweight='bold', color='darkblue', pad=20)
        
        ax.view_init(elev=current_elev, azim=current_azim)
        
        plt.draw()
        plt.pause(0.1)

# Chạy hệ thống
load_database()
threading.Thread(target=udp_listener, daemon=True).start()
update_map()