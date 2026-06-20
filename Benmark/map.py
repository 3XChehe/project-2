import pandas as pd
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- CONFIGURATION ---
TRAIN_FILE = "knn_dataset_12_grid_0.5.csv"
TEST_FILE = "test_knn_12_rectangular_with_rotation.csv"

SENSOR_COLUMNS = [
    "sensor10_0", "sensor11_0", "sensor12_0",
    "sensor20_0", "sensor21_0", "sensor22_0",
    "sensor30_0", "sensor31_0", "sensor32_0",
    "sensor40_0", "sensor41_0", "sensor42_0"
]

def run_simulation():
    print("="*60)
    print("  ĐANG HUẤN LUYỆN AI VÀ CHUẨN BỊ MÔ PHỎNG STEP-BY-STEP  ")
    print("="*60)
    
    # 1. Đọc dữ liệu
    df_train = pd.read_csv(TRAIN_FILE)
    df_test = pd.read_csv(TEST_FILE)

    # 2. Làm mịn dữ liệu TestCase bằng bộ lọc tâm Window = 5
    df_test_smoothed = df_test.copy()
    for col in SENSOR_COLUMNS:
        df_test_smoothed[col] = df_test_smoothed[col].rolling(window=5, min_periods=1, center=True).mean()
    
    # 3. Tách tập dữ liệu
    X_train = df_train[SENSOR_COLUMNS].values
    y_train = df_train[['x', 'y']].values
    X_test = df_test_smoothed[SENSOR_COLUMNS].values
    y_test = df_test[['x', 'y']].values 

    # 4. Chuẩn hóa dữ liệu sóng
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Huấn luyện mạng Nơ-ron MLP
    mlp = MLPRegressor(
        hidden_layer_sizes=(128, 64, 32), 
        activation='relu', solver='adam', max_iter=1500, random_state=42,
        early_stopping=True, validation_fraction=0.1
    )
    mlp.fit(X_train_scaled, y_train)

    # 6. Dự đoán vị trí từ AI (Tọa độ thô trước khi qua Kalman)
    y_pred_raw = mlp.predict(X_test_scaled)

    # 7. Áp dụng Kalman Filter ĐỘNG LỰC HỌC 4D (Tọa độ + Vận tốc)
    print("Đang chạy Kalman Động lực học 4D: Tự tính toán vận tốc để đuổi kịp Tag...")
    y_pred = np.zeros_like(y_pred_raw)
    
    # Trạng thái hiện tại gồm 4 biến: [x, y, vx, vy]. Ban đầu vận tốc bằng 0.
    X_state = np.array([[y_pred_raw[0, 0]], [y_pred_raw[0, 1]], [0.0], [0.0]]) 
    
    dt = 1.0 # Khoảng thời gian giữa 2 timestamp (giả định 1 giây)
    
    # Ma trận chuyển trạng thái vật lý: X = X + vx*dt
    F = np.array([
        [1.0, 0.0,  dt, 0.0],
        [0.0, 1.0, 0.0,  dt],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])
    
    # Ma trận quan sát: AI chỉ trả về Tọa độ (x,y), không trả về vận tốc
    H = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ])
    
    P = np.eye(4) * 1.0  # Hiệp phương sai lỗi ban đầu
    Q = np.eye(4) * 2.0  # Nhiễu hệ thống (bảo Kalman người có thể đổi vận tốc linh hoạt)
    R = np.eye(2) * 0.5  # Nhiễu phép đo của mạng MLP (~1.5m đến 2m)

    for t in range(len(y_pred_raw)):
        # Bước 1: Dự báo vị trí dựa trên vận tốc hiện tại
        X_state = np.dot(F, X_state)
        P = np.dot(F, np.dot(P, F.T)) + Q
        
        # Bước 2: Cập nhật dữ liệu từ AI
        Z = np.array([[y_pred_raw[t, 0]], [y_pred_raw[t, 1]]]) # Tọa độ AI đoán
        Y_residual = Z - np.dot(H, X_state)
        S = np.dot(H, np.dot(P, H.T)) + R
        K = np.dot(P, np.dot(H.T, np.linalg.inv(S))) 
        
        X_state = X_state + np.dot(K, Y_residual)
        P = P - np.dot(K, np.dot(H, P))
        
        # Lưu lại tọa độ sau lọc
        y_pred[t, 0] = X_state[0, 0]
        y_pred[t, 1] = X_state[1, 0]

    # Tính toán sai số cuối cùng
    errors = np.sqrt(np.sum((y_pred - y_test) ** 2, axis=1))
    mean_error = np.mean(errors)

    # --- 8. THIẾT LẬP ĐỒ THỊ MÔ PHỎNG ĐỘNG (ANIMATION) ---
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(-1, 22)
    ax.set_ylim(-1, 19)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlabel("Tọa độ X (Mét)", fontsize=11)
    ax.set_ylabel("Tọa độ Y (Mét)", fontsize=11)
    
    title = ax.set_title("Mô phỏng hành trình định vị Step-by-Step (Bắt đầu...)", fontsize=12, fontweight='bold')

    # Khởi tạo các cấu trúc hình học trống để cập nhật từng khung hình
    line_gt, = ax.plot([], [], 'o-', color='blue', alpha=0.3, label='Đường đi thực tế (Ground Truth)')
    line_pred, = ax.plot([], [], 's--', color='red', alpha=0.3, label='Đường đi Kalman Filter')
    
    point_gt, = ax.plot([], [], 'o', color='blue', markersize=10, label='Tag Thật hiện tại')
    point_pred, = ax.plot([], [], 's', color='red', markersize=10, label='AI đoán hiện tại')
    
    # Danh sách lưu các đường nối sai số nối giữa các bước
    error_lines = []

    # Đánh dấu cố định điểm Xuất phát và Kết thúc
    ax.scatter(y_test[0, 0], y_test[0, 1], color='green', marker='^', s=120, label='XUẤT PHÁT', zorder=5)
    ax.scatter(y_test[-1, 0], y_test[-1, 1], color='black', marker='X', s=120, label='KẾT THÚC', zorder=5)
    ax.legend(loc='upper right')

    total_frames = len(y_test)

    # Hàm vẽ từng bước (Khung hình thứ `frame`)
    def update(frame):
        # Vẽ các đoạn đường đã đi qua tính đến thời điểm hiện tại
        line_gt.set_data(y_test[:frame+1, 0], y_test[:frame+1, 1])
        line_pred.set_data(y_pred[:frame+1, 0], y_pred[:frame+1, 1])
        
        # Cập nhật vị trí nhấp nháy của con Tag ở giây hiện tại
        point_gt.set_data([y_test[frame, 0]], [y_test[frame, 1]])
        point_pred.set_data([y_pred[frame, 0]], [y_pred[frame, 1]])
        
        # Vẽ đường kết nối sai số cho bước hiện tại
        el, = ax.plot([y_test[frame, 0], y_pred[frame, 0]], 
                      [y_test[frame, 1], y_pred[frame, 1]], 
                      color='gray', linestyle=':', alpha=0.6)
        error_lines.append(el)
        
        # Cập nhật tiêu đề động hiển thị sai số tức thời của bước đó
        current_err = errors[frame]
        title.set_text(f"Mô phỏng Định vị BLE Step-by-Step\nBước: {frame+1}/{total_frames} | Sai số gói hiện tại: {current_err:.2f}m | ME Tổng: {mean_error:.2f}m")
        
        return [line_gt, line_pred, point_gt, point_pred] + error_lines

    # Khởi chạy Animation: cứ 200 mili-giây (interval=200) di chuyển 1 bước
    ani = FuncAnimation(fig, update, frames=total_frames, interval=300, blit=True, repeat=False)
    
    print("🔮 Cửa sổ mô phỏng đang hiển thị. Hãy xem con Tag di chuyển...")
    plt.show()

    # Tùy chọn: Lưu lại thành file GIF để bạn chèn vào Slide thuyết trình PowerPoint cho sinh động
    try:
        print("💾 Đang xuất video mô phỏng hành trình dạng file ảnh động GIF...")
        ani.save("positioning_simulation.gif", writer='pillow', fps=3)
        print("✨ Xuất file 'positioning_simulation.gif' thành công!")
    except Exception as e:
        print(f"Không thể lưu file GIF (Thiếu thư viện pillow): {e}")

if __name__ == "__main__":
    run_simulation()