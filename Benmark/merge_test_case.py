import pandas as pd
import numpy as np
from glob import glob
import os

# [CẤU HÌNH] Thay vì dùng 0.1, hãy dùng 0.5s (dựa trên tần số lấy mẫu 2Hz của bạn)
WINDOW = 0.5 

sensor_files = sorted(glob("tests_rectangular/*.csv"))
dfs = {}

# 1. Đọc dữ liệu
for file in sensor_files:
    name = os.path.basename(file).split(".")[0]
    df = pd.read_csv(file, header=None)
    df = df.iloc[:, :6]
    df.columns = ["timestamp", "map_id", "sensor_id", "rssi", "x", "y"]
    # Sort theo thời gian để đảm bảo tìm kiếm chính xác
    dfs[name] = df.sort_values("timestamp").reset_index(drop=True)

# 2. Chọn sensor làm gốc (Reference)
reference_name = list(dfs.keys())[0]
ref_df = dfs[reference_name]

rows = []

# 3. Merge dữ liệu
print(f"⚙️ Đang merge 12 sensor với window={WINDOW}s...")
for _, ref_row in ref_df.iterrows():
    t = ref_row["timestamp"]
    feature_vector = []
    valid = True

    for sensor_name, sensor_df in dfs.items():
        # Tìm gói tin gần nhất trong phạm vi WINDOW
        diff = (sensor_df["timestamp"] - t).abs()
        idx = diff.idxmin()
        
        if diff[idx] > WINDOW:
            valid = False
            break
        
        feature_vector.append(sensor_df.loc[idx, "rssi"])

    if not valid:
        continue

    # [CẤU HÌNH] Lấy x, y từ chính ref_row (x,y của sensor gốc)
    rows.append([t, ref_row["x"], ref_row["y"]] + feature_vector)

# 4. Lưu file
columns = ["timestamp", "x", "y"] + list(dfs.keys())
test_df = pd.DataFrame(rows, columns=columns)

test_df.to_csv("test_knn_12_rectangular_with_rotation.csv", index=False)
print(f"✅ Đã tạo xong file test_knn_12.csv với {len(test_df)} dòng dữ liệu.")