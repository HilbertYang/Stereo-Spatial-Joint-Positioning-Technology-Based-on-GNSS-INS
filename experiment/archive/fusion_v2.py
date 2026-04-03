import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from filterpy.kalman import KalmanFilter


# 解析时间戳
def parse_timestamp(line):
    try:
        timestamp = line.split(",")[0].strip()
        return pd.to_datetime(timestamp)
    except Exception as e:
        return None


# 加载GNSS数据
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
    return gnss_df


# 加载INS数据
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

    ins_df = pd.DataFrame(data, columns=["timestamp", "acc_x", "acc_y", "acc_z", "pit", "rol", "yaw", "gyr_x", "gyr_y",
                                         "gyr_z"])
    return ins_df


# 对齐INS数据和GNSS数据
def align_data(ins_df, gnss_df, time_tolerance_sec=1):
    aligned_data = []
    gnss_idx = 0
    previous_gnss_data = None

    for i, ins_row in ins_df.iterrows():
        ins_time = ins_row['timestamp']

        while gnss_idx < len(gnss_df) and gnss_df.iloc[gnss_idx]['timestamp'] < ins_time:
            previous_gnss_data = gnss_df.iloc[gnss_idx]
            gnss_idx += 1

        if gnss_idx < len(gnss_df) and abs(
                (gnss_df.iloc[gnss_idx]['timestamp'] - ins_time).total_seconds()) <= time_tolerance_sec:
            aligned_data.append([*ins_row, *gnss_df.iloc[gnss_idx][['longitude', 'latitude', 'altitude']]])
        elif previous_gnss_data is not None:
            aligned_data.append([*ins_row, *previous_gnss_data[['longitude', 'latitude', 'altitude']]])

    aligned_df = pd.DataFrame(aligned_data,
                              columns=["timestamp", "acc_x", "acc_y", "acc_z", "pit", "rol", "yaw", "gyr_x", "gyr_y",
                                       "gyr_z", "longitude", "latitude", "altitude"])
    return aligned_df


# 扩展卡尔曼滤波设置
def setup_extended_kalman_filter(initial_state):
    kf = KalmanFilter(dim_x=15, dim_z=6)  # 15维状态，6维观测（经度、纬度、高度、加速度）

    dt = 1  # 假设每个时间步为 1 秒

    def h(x):
        z = np.array([x[0], x[1], x[2], x[12], x[13], x[14]])  # 观测方程
        return z

    # 设置初始状态
    kf.x = np.array(initial_state)
    kf.P = np.eye(15) * 500  # 初始协方差矩阵
    kf.R = np.diag([0.001, 0.001, 0.01, 0.1, 0.1, 0.1])  # 观测噪声矩阵
    kf.Q = np.eye(15) * 0.01  # 过程噪声矩阵

    return kf, h


# 扩展卡尔曼滤波更新过程
def run_extended_kalman_filter(kf, h, aligned_df):
    estimated_positions = []
    previous_time = None

    for _, row in aligned_df.iterrows():
        # 动态时间步长 dt
        current_time = row["timestamp"]
        if previous_time is not None:
            dt = (current_time - previous_time).total_seconds()
            dt = max(0.1, min(dt, 1.0))  # 限制 dt 范围
        else:
            dt = 1
        previous_time = current_time

        # 状态转移矩阵 F
        kf.F = np.eye(15)
        kf.F[0, 3] = dt
        kf.F[1, 4] = dt
        kf.F[2, 5] = dt
        kf.F[3, 12] = dt
        kf.F[4, 13] = dt
        kf.F[5, 14] = dt

        # 预测步骤
        kf.predict()

        # 观测矩阵 H
        kf.H = np.zeros((6, 15))
        kf.H[0, 0] = 1
        kf.H[1, 1] = 1
        kf.H[2, 2] = 1
        kf.H[3, 12] = 1
        kf.H[4, 13] = 1
        kf.H[5, 14] = 1

        # 观测数据
        z = np.array([row["longitude"], row["latitude"], row["altitude"],
                      row["acc_x"], row["acc_y"], row["acc_z"]])
        kf.update(z)

        # 保存估计位置
        estimated_positions.append([kf.x[0], kf.x[1], kf.x[2]])

    return np.array(estimated_positions)


# 绘制三维轨迹
def plot_3d_trajectory(estimated_positions, gnss_data):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制估计的轨迹
    ax.plot(estimated_positions[:, 0], estimated_positions[:, 1], estimated_positions[:, 2],
            label='Estimated Trajectory', color='b', linestyle='-', marker='o')

    # 绘制GNSS数据
    ax.scatter(gnss_data["longitude"], gnss_data["latitude"], gnss_data["altitude"],
               label='GNSS Data', color='r', s=50)

    # 设置标签
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Altitude')
    ax.set_title('3D Trajectory (Estimated vs GNSS)')
    ax.legend()
    plt.show()


# 主函数
def main():
    # 读取GNSS数据和INS数据
    gnss_data = load_gnss_data('../processed_bd.txt')
    ins_data = load_ins_data('../processed_gd.txt')

    # 对齐INS数据和GNSS数据
    aligned_data = align_data(ins_data, gnss_data)

    # 使用简单的低通滤波器对加速度数据平滑
    aligned_data["acc_x"] = aligned_data["acc_x"].rolling(window=5, center=True).mean()
    aligned_data["acc_y"] = aligned_data["acc_y"].rolling(window=5, center=True).mean()
    aligned_data["acc_z"] = aligned_data["acc_z"].rolling(window=5, center=True).mean()
    aligned_data = aligned_data.dropna()  # 滤波会产生NaN，需删除

    # 初始化滤波器
    initial_state = [
        aligned_data["longitude"].iloc[0], aligned_data["latitude"].iloc[0], aligned_data["altitude"].iloc[0],
        0.01, 0.01, 0.01,  # 初始速度 x, y, z
        0, 0, 0,           # 初始俯仰角、滚转角、偏航角
        0, 0, 0,           # 初始角速度
        0.01, 0.01, 0.01   # 初始加速度 x, y, z
    ]
    kf, h = setup_extended_kalman_filter(initial_state)

    # 执行扩展卡尔曼滤波
    estimated_positions = run_extended_kalman_filter(kf, h, aligned_data)
    print("Estimated Positions:", estimated_positions)

    # 绘制三维轨迹
    plot_3d_trajectory(estimated_positions, gnss_data)


if __name__ == '__main__':
    main()
