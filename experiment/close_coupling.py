"""
紧耦合 GNSS-INS 融合
---------------------
状态向量 (15维): [lon, lat, alt, vlon, vlat, valt, alon, alat, aalt, pit, rol, yaw, gyr_x, gyr_y, gyr_z]
观测向量 (6维):  [lon, lat, alt, acc_x, acc_y, acc_z]
- GNSS 位置 + INS 加速度同时作为观测量
"""

import numpy as np
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter
from utils import load_gnss_data, load_ins_data, filter_altitude_outliers, align_data


def _build_kalman_filter(initial_state, dt=1.0):
    kf = KalmanFilter(dim_x=15, dim_z=6)

    kf.F = np.array([
        [1, 0, 0, dt, 0,  0,  0.5*dt**2, 0,        0,        0, 0, 0, 0, 0, 0],  # lon
        [0, 1, 0, 0,  dt, 0,  0,         0.5*dt**2, 0,        0, 0, 0, 0, 0, 0],  # lat
        [0, 0, 1, 0,  0,  dt, 0,         0,         0.5*dt**2, 0, 0, 0, 0, 0, 0],  # alt
        [0, 0, 0, 1,  0,  0,  dt,        0,         0,        0, 0, 0, 0, 0, 0],  # vlon
        [0, 0, 0, 0,  1,  0,  0,         dt,        0,        0, 0, 0, 0, 0, 0],  # vlat
        [0, 0, 0, 0,  0,  1,  0,         0,         dt,       0, 0, 0, 0, 0, 0],  # valt
        [0, 0, 0, 0,  0,  0,  1,         0,         0,        0, 0, 0, 0, 0, 0],  # acc_x
        [0, 0, 0, 0,  0,  0,  0,         1,         0,        0, 0, 0, 0, 0, 0],  # acc_y
        [0, 0, 0, 0,  0,  0,  0,         0,         1,        0, 0, 0, 0, 0, 0],  # acc_z
        [0, 0, 0, 0,  0,  0,  0,         0,         0,        1, 0, 0, 0, 0, 0],  # pit
        [0, 0, 0, 0,  0,  0,  0,         0,         0,        0, 1, 0, 0, 0, 0],  # rol
        [0, 0, 0, 0,  0,  0,  0,         0,         0,        0, 0, 1, 0, 0, 0],  # yaw
        [0, 0, 0, 0,  0,  0,  0,         0,         0,        0, 0, 0, 1, 0, 0],  # gyr_x
        [0, 0, 0, 0,  0,  0,  0,         0,         0,        0, 0, 0, 0, 1, 0],  # gyr_y
        [0, 0, 0, 0,  0,  0,  0,         0,         0,        0, 0, 0, 0, 0, 1],  # gyr_z
    ])

    # 观测矩阵：GNSS位置(前3行) + INS加速度(后3行)
    kf.H = np.zeros((6, 15))
    kf.H[0, 0] = 1  # lon
    kf.H[1, 1] = 1  # lat
    kf.H[2, 2] = 1  # alt
    kf.H[3, 6] = 1  # acc_x
    kf.H[4, 7] = 1  # acc_y
    kf.H[5, 8] = 1  # acc_z

    kf.P *= 500
    kf.R = np.eye(6) * 20
    kf.Q = np.eye(15) * 0.01

    kf.x = np.array(initial_state, dtype=float)
    return kf


def fuse(merged_data, dt=1.0):
    row0 = merged_data.iloc[0]
    initial_state = [
        row0["longitude"], row0["latitude"], row0["altitude"],
        0, 0, 0,   # 初始速度
        0, 0, 0,   # 初始加速度
        0, 0, 0,   # 初始姿态角
        0, 0, 0,   # 初始角速度
    ]

    kf = _build_kalman_filter(initial_state, dt)
    fused_positions = []

    for _, row in merged_data.iterrows():
        z = np.array([
            row["longitude"], row["latitude"], row["altitude"],
            row["acc_x"], row["acc_y"], row["acc_z"],
        ])
        kf.predict()
        kf.update(z)
        fused_positions.append(kf.x[:3].copy())

    return np.array(fused_positions)


def plot(gnss_clean, gnss_outliers, fused_positions):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(gnss_clean["longitude"], gnss_clean["latitude"], gnss_clean["altitude"],
               label="GNSS Normal", color="r", s=5)
    ax.scatter(gnss_outliers["longitude"], gnss_outliers["latitude"], gnss_outliers["altitude"],
               label="GNSS Outliers", color="orange", s=20, marker='x')
    ax.plot(fused_positions[:, 0], fused_positions[:, 1], fused_positions[:, 2],
            label="Fused (Close)", color="b", linewidth=2)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Altitude')
    ax.set_title("Close Coupling: GNSS-INS Fusion")
    ax.legend()
    plt.show()


def plot_errors(gnss_clean, fused_positions):
    n = len(fused_positions)
    timestamps = gnss_clean["timestamp"].iloc[:n]
    lon_err = gnss_clean["longitude"].iloc[:n].values - fused_positions[:, 0]
    lat_err = gnss_clean["latitude"].iloc[:n].values - fused_positions[:, 1]
    alt_err = gnss_clean["altitude"].iloc[:n].values - fused_positions[:, 2]

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].plot(timestamps, lon_err, color='r', label="Longitude Error")
    axes[0].set_ylabel("Error (°)")
    axes[0].legend()
    axes[0].grid()

    axes[1].plot(timestamps, lat_err, color='g', label="Latitude Error")
    axes[1].set_ylabel("Error (°)")
    axes[1].legend()
    axes[1].grid()

    axes[2].plot(timestamps, alt_err, color='b', label="Altitude Error")
    axes[2].set_ylabel("Error (m)")
    axes[2].set_xlabel("Timestamp")
    axes[2].legend()
    axes[2].grid()

    plt.suptitle("Close Coupling Fusion Errors")
    plt.show()


def main():
    gnss_df = load_gnss_data("processed_bd.txt")
    ins_df = load_ins_data("processed_gd.txt")

    gnss_clean, gnss_outliers = filter_altitude_outliers(gnss_df)
    merged = align_data(gnss_clean, ins_df, tolerance_sec=2)

    fused_positions = fuse(merged)
    plot(gnss_clean, gnss_outliers, fused_positions)
    plot_errors(gnss_clean, fused_positions)


if __name__ == "__main__":
    main()
