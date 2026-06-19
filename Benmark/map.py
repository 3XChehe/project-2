import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import threading
import time

TRAIN_FILE = "knn_dataset_12.csv"
TEST_FILE = "test_knn_12.csv"

current_pos = [0.0, 0.0]
ground_truth = [0.0, 0.0]

trajectory_pred = []
trajectory_gt = []
current_error = 0
# =========================
# TRAIN KNN
# =========================
fingerprint_db = []
feature_columns = []

def load_database():

    global fingerprint_db
    global feature_columns

    df = pd.read_csv(TRAIN_FILE)

    feature_columns = [
        c for c in df.columns
        if c not in ["x","y"]
    ]

    print(
        "Using",
        len(feature_columns),
        "sensors"
    )

    grouped = {}
    for _, row in df.iterrows():

        coord = (
            float(row["x"]),
            float(row["y"])
        )

        feature = row[
            feature_columns
        ].values.astype(float)

        if coord not in grouped:
            grouped[coord] = []

        grouped[coord].append(feature)

    fingerprint_db = list(
        grouped.items()
    )

    print(
        f"Loaded {len(fingerprint_db)} coordinates"
    )

sensor_pos = {

    "sensor10": (7.00, 7.09),
    "sensor11": (7.18, 0.68),
    "sensor12": (0.71, 6.16),

    "sensor20": (7.25, 11.36),
    "sensor21": (0.76, 12.13),
    "sensor22": (7.18, 17.64),

    "sensor30": (13.14, 12.33),
    "sensor31": (12.82, 16.83),
    "sensor32": (18.12, 11.93),

    "sensor40": (13.01, 5.51),
    "sensor41": (17.77, 6.33),
    "sensor42": (12.76, 0.27)
}

def predict_position(rssi_vector):

    # ==========================
    # Chọn 3 sensor RSSI mạnh nhất
    # ==========================

    strongest_idx = np.argsort(
        rssi_vector
    )[-3:]
    
    selected = [
        feature_columns[i]
        for i in strongest_idx
    ]

    print(
        "Using:",
        selected
    )

    feature = np.array(
        rssi_vector
    )[strongest_idx]

    distances = []

    for coord, feature_list in fingerprint_db:

        best_dist = float("inf")

        for db_feature in feature_list:

            db_sub = db_feature[
                strongest_idx
            ]

            dist = np.linalg.norm(
                feature - db_sub
            )

            if dist < best_dist:
                best_dist = dist

        distances.append(
            (
                best_dist,
                coord
            )
        )

    distances.sort(
        key=lambda x: x[0]
    )

    K = 5

    neighbors = distances[:K]

    weights = [
        1/(d+0.001)
        for d,_ in neighbors
    ]

    total_w = sum(weights)

    px = sum(
        neighbors[i][1][0] *
        weights[i]
        for i in range(K)
    ) / total_w

    py = sum(
        neighbors[i][1][1] *
        weights[i]
        for i in range(K)
    ) / total_w

    return px, py
# =========================
# REALTIME REPLAY
# =========================

def replay_test():

    global current_pos
    global ground_truth

    df = pd.read_csv(TEST_FILE)

    prev_time = None

    SPEEDUP = 2

    errors = []

    for _, row in df.iterrows():

        ts = row["timestamp"]

        if prev_time is not None:

            dt = ts - prev_time

            time.sleep(
                max(
                    dt / SPEEDUP,
                    0.01
                )
            )

        prev_time = ts

        rssi = row[
            feature_columns
        ].values.astype(float)

        px, py = predict_position(
            rssi
        )

        current_pos[0] = px
        current_pos[1] = py

        trajectory_pred.append(
            (px, py)
        )

        trajectory_gt.append(
            (
                row["x"],
                row["y"]
            )
        )

        ground_truth[0] = row["x"]
        ground_truth[1] = row["y"]

        err = np.sqrt(
            (px-row["x"])**2 +
            (py-row["y"])**2
        )
        global current_error
        current_error = err

        errors.append(err)

        print(
            f"GT=({row['x']:.2f},{row['y']:.2f}) "
            f"PRED=({px:.2f},{py:.2f}) "
            f"ERR={err:.2f}m"
        )

    print("\n===== RESULT =====")

    print(
        "Mean Error:",
        np.mean(errors)
    )

    print(
        "RMSE:",
        np.sqrt(
            np.mean(
                np.square(errors)
            )
        )
    )

# =========================
# MAP
# =========================

dongles = {

    "sensor10": (7.00, 7.09),
    "sensor11": (7.18, 0.68),
    "sensor12": (0.71, 6.16),

    "sensor20": (7.25, 11.36),
    "sensor21": (0.76, 12.13),
    "sensor22": (7.18, 17.64),

    "sensor30": (13.14, 12.33),
    "sensor31": (12.82, 16.83),
    "sensor32": (18.12, 11.93),

    "sensor40": (13.01, 5.51),
    "sensor41": (17.77, 6.33),
    "sensor42": (12.76, 0.27)
}

plt.ion()

fig, ax = plt.subplots(
    figsize=(9,9)
)

def update_map():

    while True:

        ax.clear()

        ax.set_xlim(0,20)
        ax.set_ylim(0,20)

        ax.grid(True)

        ax.set_title(
            f"Realtime Fingerprinting\n"
            f"Error = {current_error:.2f} m"
        )

        for name,(x,y) in dongles.items():

            ax.scatter(
                x,
                y,
                c='blue',
                s=200,
                marker='^'
            )

            ax.text(
                x+0.2,
                y+0.2,
                name
            )

        if len(trajectory_gt) > 1:

            ax.plot(
                [p[0] for p in trajectory_gt],
                [p[1] for p in trajectory_gt],
                'g--',
                linewidth=2
            )

        if len(trajectory_pred) > 1:

            ax.plot(
                [p[0] for p in trajectory_pred],
                [p[1] for p in trajectory_pred],
                'r-',
                linewidth=2
            )

        # Ground Truth

        ax.scatter(
            ground_truth[0],
            ground_truth[1],
            c='green',
            s=120,
            label='Ground Truth'
        )

        # Prediction

        ax.scatter(
            current_pos[0],
            current_pos[1],
            c='red',
            s=200,
            marker='*',
            label='Prediction'
        )

        ax.legend()

        plt.draw()
        plt.pause(0.05)

# =========================
# MAIN
# =========================

load_database()

threading.Thread(
    target=replay_test,
    daemon=True
).start()

update_map()