import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

ROOM_WIDTH = 382
ROOM_HEIGHT = 420

fig, ax = plt.subplots(figsize=(6, 8))

# Giới hạn trục
ax.set_xlim(-20, ROOM_WIDTH + 20)
ax.set_ylim(0, ROOM_HEIGHT + 20)



# Khung phòng
room = patches.Rectangle(
    (0, 0),
    ROOM_WIDTH,
    ROOM_HEIGHT,
    linewidth=2,
    edgecolor='black',
    facecolor='none'
)

ax.add_patch(room)

# =========================
# Các vật thể
# =========================

objects = [
    (100, 0, 148, 50, 'red', 'tu1'),
    (0, 16, 64, 181, 'blue', 'tu2'),
    (9, 197, 52, 40, 'green', 'tu3'),
    (5, 265, 200, 155, 'orange', 'giuong'),
    (328, 243, 54, 123, 'purple', 'tu5'),
    (312, 123, 70, 120, 'cyan', 'ban')
]

for x, y, w, h, color, label in objects:
    rect = patches.Rectangle(
        (x, y),
        w,
        h,
        linewidth=1,
        edgecolor=color,
        facecolor=color,
        alpha=0.5,
        label=label
    )

    ax.add_patch(rect)

# =========================
# Beacon / Sensor points
# =========================

S1 = np.array([257, 0])
S2 = np.array([0, 222])
S3 = np.array([236, 420])

# Vẽ điểm
ax.scatter(
    [S1[0], S2[0], S3[0]],
    [S1[1], S2[1], S3[1]],
    c='black',
    s=100,
    marker='o',
    label='Scanners'
)

# Gắn nhãn
ax.text(S3[0] + 5, S3[1] + 5, 'S1', fontsize=12)
ax.text(S1[0] + 5, S1[1] + 5, 'S2', fontsize=12)
ax.text(S2[0] + 5, S2[1] + 5, 'S3', fontsize=12)

# =========================

ax.set_aspect('equal')
#ax.grid(True)
ax.legend()

plt.show()