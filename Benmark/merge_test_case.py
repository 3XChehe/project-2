import pandas as pd
import numpy as np
from glob import glob
import os

WINDOW = 0.1

sensor_files = sorted(
    glob("tests/*.csv")
)

dfs = {}

for file in sensor_files:

    name = os.path.basename(file).split(".")[0]

    df = pd.read_csv(
        file,
        header=None
    )

    df = df.iloc[:, :6]

    df.columns = [
        "timestamp",
        "map_id",
        "sensor_id",
        "rssi",
        "x",
        "y"
    ]

    dfs[name] = df

reference_name = list(dfs.keys())[0]
ref_df = dfs[reference_name]

rows = []

for _, ref_row in ref_df.iterrows():

    t = ref_row["timestamp"]

    feature_vector = []

    valid = True

    for sensor_name, sensor_df in dfs.items():

        idx = (
            sensor_df["timestamp"] - t
        ).abs().idxmin()

        row = sensor_df.loc[idx]

        if abs(row["timestamp"] - t) > WINDOW:

            valid = False
            break

        feature_vector.append(
            row["rssi"]
        )

    if not valid:
        continue

    rows.append(
        [t,
         ref_row["x"],
         ref_row["y"]] +
         feature_vector
    )

columns = (
    ["timestamp", "x", "y"]
    + list(dfs.keys())
)

test_df = pd.DataFrame(
    rows,
    columns=columns
)

test_df.to_csv(
    "test_knn_12.csv",
    index=False
)

print(test_df.head())