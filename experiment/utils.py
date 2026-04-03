import re
import numpy as np
import pandas as pd


def parse_timestamp(line):
    match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line)
    return match.group(0) if match else None


def load_gnss_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if "'E" in line and "'N" in line:
                timestamp = parse_timestamp(line)
                if timestamp:
                    parts = line.split(",")
                    try:
                        longitude = float(re.sub(r"'E", "", parts[1].strip()))
                        latitude = float(re.sub(r"'N", "", parts[2].strip()))
                        altitude = float(re.sub(r"m", "", parts[3].strip()))
                        data.append([timestamp, longitude, latitude, altitude])
                    except (IndexError, ValueError):
                        continue
    gnss_df = pd.DataFrame(data, columns=["timestamp", "longitude", "latitude", "altitude"])
    gnss_df["timestamp"] = pd.to_datetime(gnss_df["timestamp"])
    return gnss_df


def load_ins_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if "acc_x" in line:
                timestamp = parse_timestamp(line)
                if timestamp:
                    parts = line.split(", ")
                    try:
                        pit = float(parts[0].split(":")[1].strip())
                        rol = float(parts[1].split(":")[1].strip())
                        yaw = float(parts[2].split(":")[1].strip())
                        acc_x = float(parts[4].split(":")[1].strip())
                        acc_y = float(parts[5].split(":")[1].strip())
                        acc_z = float(parts[6].split(":")[1].strip())
                        gyr_x = float(parts[7].split(":")[1].strip())
                        gyr_y = float(parts[8].split(":")[1].strip())
                        gyr_z = float(parts[9].split(":")[1].strip())
                        data.append([timestamp, acc_x, acc_y, acc_z, pit, rol, yaw, gyr_x, gyr_y, gyr_z])
                    except (IndexError, ValueError):
                        continue
    ins_df = pd.DataFrame(
        data,
        columns=["timestamp", "acc_x", "acc_y", "acc_z", "pit", "rol", "yaw", "gyr_x", "gyr_y", "gyr_z"]
    )
    ins_df["timestamp"] = pd.to_datetime(ins_df["timestamp"])
    return ins_df


def filter_altitude_outliers(df, window=3, z_thresh=2):
    df["alt_med"] = df["altitude"].rolling(window=window, center=True).median()
    df["alt_dev"] = (df["altitude"] - df["alt_med"]).abs()
    alt_dev_thresh = df["alt_dev"].mean() + z_thresh * df["alt_dev"].std()

    df["alt_diff_prev"] = df["altitude"].diff().abs()
    df["alt_diff_next"] = df["altitude"].diff(-1).abs()
    alt_diff_thresh = df["alt_diff_prev"].mean() + z_thresh * df["alt_diff_prev"].std()

    condition = (
        (df["alt_dev"] < alt_dev_thresh) &
        (df["alt_diff_prev"] < alt_diff_thresh) &
        (df["alt_diff_next"] < alt_diff_thresh)
    )

    normal_df = df[condition].copy()
    outliers_df = df[~condition].copy()

    aux_cols = ["alt_med", "alt_dev", "alt_diff_prev", "alt_diff_next"]
    normal_df.drop(columns=aux_cols, inplace=True)
    outliers_df.drop(columns=aux_cols, inplace=True)

    print(f"Filtered {len(outliers_df)} altitude outliers.")
    return normal_df, outliers_df


def align_data(gnss_df, ins_df, tolerance_sec=2):
    aligned = pd.merge_asof(
        gnss_df.sort_values("timestamp"),
        ins_df.sort_values("timestamp"),
        on="timestamp",
        tolerance=pd.Timedelta(f'{tolerance_sec}s')
    )
    print(f"Aligned {len(aligned)} data points.")
    return aligned
