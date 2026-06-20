import ast
import pandas as pd
import numpy as np
from glob import glob
import os

RSSI_VALUES = np.arange(-100, -19)

def expected_rssi(hist):
    hist = np.array(hist, dtype=float)
    return np.sum(hist * RSSI_VALUES)

def load_sensor_file(path):

    sensor_name = os.path.basename(path).split(".")[0]

    data = {}

    with open(path, "r") as f:

        lines = f.readlines()[1:]

        for line in lines:

            pos, beacon, hist = line.strip().split("::")

            pos = tuple(ast.literal_eval(pos))
            hist = ast.literal_eval(hist)

            data[pos] = expected_rssi(hist)

    return sensor_name, data


sensor_files = sorted(
    glob("fingerprints_grid_0.5/*.txt")
)
all_sensors = {}
common_positions = None

for file in sensor_files:

    name, data = load_sensor_file(file)

    all_sensors[name] = data

    pos_set = set(data.keys())

    if common_positions is None:
        common_positions = pos_set
    else:
        common_positions &= pos_set


rows = []

for pos in common_positions:

    row = [pos[0], pos[1]]

    for sensor_name in sorted(all_sensors.keys()):

        row.append(
            all_sensors[sensor_name][pos]
        )

    rows.append(row)

columns = ["x", "y"] + sorted(all_sensors.keys())

df = pd.DataFrame(
    rows,
    columns=columns
)

df.to_csv(
    "knn_dataset_12_grid_0.5.csv",
    index=False
)

print(df.head())
print("Samples =", len(df))