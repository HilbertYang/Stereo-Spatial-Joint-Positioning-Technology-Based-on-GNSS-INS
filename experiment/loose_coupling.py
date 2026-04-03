"""
松耦合 GNSS-INS 融合
---------------------
状态向量 (9维): [lon, lat, alt, vlon, vlat, valt, alon, alat, aalt]
- GNSS 位置作为观测量 (3维)
- INS 加速度通过控制输入矩阵 B 驱动状态预测
"""

import numpy as np
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter
from utils import load_gnss_data, load_ins_data, filter_altitude_outliers, align_data


def _build_kalman_filter(initial_pos, dt=1.0):
    kf = KalmanFilter(dim_x=9, dim_z=3)

    kf.F = np.array([
        [1, 0, 0, dt, 0,  0,  0.5*dt**2, 0,        0       ],
        [0, 1, 0, 0,  dt, 0,  0,         0.5*dt**2, 0       ],
        [0, 0, 1, 0,  0,  dt, 0,         0,         0.5*dt**2],
        [0, 0, 0, 1,  0,  0,  dt,        0,         0       ],
        [0, 0, 0, 0,  1,  0,  0,         dt,        0       ],
        [0, 0, 0, 0,  0,  1,  0,         0,         dt      ],
        [0, 0, 0, 0,  0,  0,  1,         0,         0       ],
        [0, 0, 0, 0,  0,  0,  0,         1,         0       ],
        [0, 0, 0, 0,  0,  0,  0,         0,         1       ],
    ])

    # 控制输入矩阵：加速度影响位置和速度
    kf.B = np.zeros((9, 3))
    for i in range(3):
        kf.B[i, i] = 0.5 * dt**2   # 加速度对位置的影响
        kf.B[i + 3, i] = dt         # 加速度对速度的影响

    kf.H = np.eye(3, 9)  # 只观测位置

    kf.P *= 500
    kf.R = np.eye(3) * 10
    kf.Q = np.eye(9) * 0.1

    kf.x = np.zeros(9)
    kf.x[:3] = initial_pos
    return kf


def fuse(merged_data, dt=1.0):
    initial_pos = merged_data.iloc[0][["longitude", "latitude", "altitude"]].to_numpy()
    kf = _build_kalman_filter(initial_pos, dt)

    fused_positions = []
    for _, row in merged_data.iterrows():
        acc = np.array([row["acc_x"], row["acc_y"], row["acc_z"]])
        z = row[["longitude", "latitude", "altitude"]].to_numpy()

        kf.predict(u=acc)
        kf.update(z)
        fused_positions.append(kf.x[:3].copy())

    return np.array(fused_positions)


def plot(gnss_clean, gnss_outliers, fused_positions):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(gnss_clean["longitude"], gnss_clean["latitude"], gnss_clean["altitude"],
               label="GNSS Normal", color="r", s=10)
    ax.scatter(gnss_outliers["longitude"], gnss_outliers["latitude"], gnss_outliers["altitude"],
               label="GNSS Outliers", color="orange", s=20, marker='x')
    ax.plot(fused_positions[:, 0], fused_positions[:, 1], fused_positions[:, 2],
            label="Fused (Loose)", color="b", linewidth=2)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Altitude')
    ax.set_title("Loose Coupling: GNSS-INS Fusion")
    ax.legend()
    plt.show()


def main():
    gnss_df = load_gnss_data("processed_bd.txt")
    ins_df = load_ins_data("processed_gd.txt")

    gnss_clean, gnss_outliers = filter_altitude_outliers(gnss_df)
    merged = align_data(gnss_clean, ins_df, tolerance_sec=1)

    fused_positions = fuse(merged)
    plot(gnss_clean, gnss_outliers, fused_positions)


if __name__ == "__main__":
    main()
