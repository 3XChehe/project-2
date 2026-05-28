import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import socket

# Thiết lập 3 scanner
S2 = np.array([230, 0])
S1 = np.array([250, 420])
S3 = np.array([0, 190])

ROOM_WIDTH = 370
ROOM_HEIGHT = 420

# Danh sách vật thể cố định
OBJECTS = [
    (100, 0, 148, 50, 'red', 'tu1'),
    (0, 16, 64, 181, 'blue', 'tu2'),
    (9, 197, 52, 40, 'green', 'tu3'),
    (5, 265, 200, 155, 'orange', 'giuong'),
    (328, 243, 54, 123, 'purple', 'tu5'),
    (312, 123, 70, 120, 'cyan', 'ban')
]

def trilateration(d1, d2, d3):
    p1, p2, p3 = S1, S2, S3
    A = np.array([
        [2 * (p2[0] - p1[0]), 2 * (p2[1] - p1[1])],
        [2 * (p3[0] - p2[0]), 2 * (p3[1] - p2[1])]
    ])
    b = np.array([
        d1**2 - d2**2 - p1[0]**2 - p1[1]**2 + p2[0]**2 + p2[1]**2,
        d2**2 - d3**2 - p2[0]**2 - p2[1]**2 + p3[0]**2 + p3[1]**2
    ])
    try:
        return np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None

# Cấu hình socket
UDP_IP = "127.0.0.1"
UDP_PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

plt.ion()
fig, ax = plt.subplots(figsize=(6, 8))

print("Python đang chờ dữ liệu từ Server C...")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')
        parts = message.split(',')
        if len(parts) == 3:
            d1, d2, d3 = float(parts[0]), float(parts[1]), float(parts[2])
            tag_pos = trilateration(d1, d2, d3)
        else:
            continue

        ax.clear()
        ax.set_xlim(-50, ROOM_WIDTH + 50)
        ax.set_ylim(-50, ROOM_HEIGHT + 50)
        
        # 1. Vẽ khung phòng
        ax.add_patch(patches.Rectangle((0, 0), ROOM_WIDTH, ROOM_HEIGHT, fill=False, color='black', lw=2))
        
        # 2. Vẽ vật thể
        for x, y, w, h, color, label in OBJECTS:
            rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor=color, facecolor=color, alpha=0.3)
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, label, fontsize=7, ha='center', va='center')

        # 3. Vẽ Scanners
        ax.scatter([S1[0], S2[0], S3[0]], [S1[1], S2[1], S3[1]], c='red', s=100, label='Scanners')
        
        # 4. Vẽ Tag và vòng tròn
        if tag_pos is not None:
            ax.scatter(tag_pos[0], tag_pos[1], c='blue', s=200, marker='*', label='Tag')
            ax.add_patch(plt.Circle(S1, d1, color='red', fill=False, linestyle='--', alpha=0.2))
            ax.add_patch(plt.Circle(S2, d2, color='red', fill=False, linestyle='--', alpha=0.2))
            ax.add_patch(plt.Circle(S3, d3, color='red', fill=False, linestyle='--', alpha=0.2))

        plt.title("Hệ thống định vị BLE thực tế")
        plt.draw()
        plt.pause(0.01)

    except BlockingIOError:
        plt.pause(0.1)
    except Exception as e:
        print(f"Lỗi: {e}")
        plt.pause(0.1)