import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from filterpy.kalman import KalmanFilter


# 解析时间戳
def parse_timestamp(line):
    # 假设时间戳格式为 '2024-12-13 21:15:14.420'
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
    gnss_df["timestamp"] = pd.to_datetime(gnss_df["timestamp"])
    return gnss_df


# 加载INS数据
def load_ins_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if "acc_x" in line:  # 确保行中有加速度数据
                timestamp = parse_timestamp(line)
                if timestamp:
                    parts = line.split(", ")
                    try:
                        # 提取角度数据（俯仰、滚转、偏航）
                        pit = float(parts[0].split(":")[1].strip())  # 假设第一列为俯仰角
                        rol = float(parts[1].split(":")[1].strip())  # 假设第二列为滚转角
                        yaw = float(parts[2].split(":")[1].strip())  # 假设第三列为偏航角

                        # 提取加速度数据
                        acc_x = float(parts[4].split(":")[1].strip())
                        acc_y = float(parts[5].split(":")[1].strip())
                        acc_z = float(parts[6].split(":")[1].strip())

                        # 提取陀螺仪数据
                        gyr_x = float(parts[7].split(":")[1].strip())  # 假设第八列为陀螺仪X轴数据
                        gyr_y = float(parts[8].split(":")[1].strip())  # 假设第九列为陀螺仪Y轴数据
                        gyr_z = float(parts[9].split(":")[1].strip())  # 假设第十列为陀螺仪Z轴数据

                        # 将数据添加到列表中
                        data.append([timestamp, acc_x, acc_y, acc_z, pit, rol, yaw, gyr_x, gyr_y, gyr_z])
                    except (IndexError, ValueError):
                        continue

    # 将数据转化为DataFrame
    ins_df = pd.DataFrame(data, columns=["timestamp", "acc_x", "acc_y", "acc_z", "pit", "rol", "yaw", "gyr_x", "gyr_y",
                                         "gyr_z"])
    ins_df["timestamp"] = pd.to_datetime(ins_df["timestamp"])  # 转换时间戳
    return ins_df


# 对齐INS数据和GNSS数据
def align_data(ins_df, gnss_df, time_tolerance_sec=1):
    aligned_data = []
    gnss_idx = 0
    previous_gnss_data = None

    for i, ins_row in ins_df.iterrows():
        ins_time = ins_row['timestamp']

        # 找到距离INS时间最近的GNSS数据
        while gnss_idx < len(gnss_df) and gnss_df.iloc[gnss_idx]['timestamp'] < ins_time:
            previous_gnss_data = gnss_df.iloc[gnss_idx]
            gnss_idx += 1

        if gnss_idx < len(gnss_df) and abs(
                (gnss_df.iloc[gnss_idx]['timestamp'] - ins_time).total_seconds()) <= time_tolerance_sec:
            # 如果找到了合适的GNSS数据
            aligned_data.append([*ins_row, *gnss_df.iloc[gnss_idx][['longitude', 'latitude', 'altitude']]])
        elif previous_gnss_data is not None:
            # 如果没有GNSS数据，则使用上一条有效的GNSS数据
            aligned_data.append([*ins_row, *previous_gnss_data[['longitude', 'latitude', 'altitude']]])

    aligned_df = pd.DataFrame(aligned_data,
                              columns=["timestamp", "acc_x", "acc_y", "acc_z", "pit", "rol", "yaw", "gyr_x", "gyr_y",
                                       "gyr_z", "longitude", "latitude", "altitude"])
    return aligned_df


# 过滤高度异常值：结合局部窗口平滑与上下文高度检测
def filter_altitude_outliers(df, window=3, z_thresh=2):
    # 计算局部高度中值
    df["alt_med"] = df["altitude"].rolling(window=window, center=True).median()

    # 计算当前高度与局部中值的偏差
    df["alt_dev"] = (df["altitude"] - df["alt_med"]).abs()

    # 设定偏差阈值
    alt_dev_thresh = df["alt_dev"].mean() + z_thresh * df["alt_dev"].std()

    # 检查上下文高度：当前点与前后点的高度差
    df["alt_diff_prev"] = df["altitude"].diff().abs()
    df["alt_diff_next"] = df["altitude"].diff(-1).abs()

    # 上下文阈值
    alt_diff_thresh = df["alt_diff_prev"].mean() + z_thresh * df["alt_diff_prev"].std()

    # 筛选条件：偏差与高度突变检测
    condition = (
        (df["alt_dev"] < alt_dev_thresh) &
        (df["alt_diff_prev"] < alt_diff_thresh) &
        (df["alt_diff_next"] < alt_diff_thresh)
    )

    # 分离正常点和异常点
    normal_df = df[condition].copy()
    outliers_df = df[~condition].copy()

    # 清理辅助列
    for col in ["alt_med", "alt_dev", "alt_diff_prev", "alt_diff_next"]:
        normal_df.drop(columns=col, inplace=True)
        outliers_df.drop(columns=col, inplace=True)

    print(f"Filtered {len(outliers_df)} altitude outliers.")
    return normal_df, outliers_df

def setup_kalman_filter_with_ins_gnss(initial_state):
    kf = KalmanFilter(dim_x=15, dim_z=6)  # 15维状态，6维观测（经度、纬度、高度、加速度、角速度）
    dt = 1  # 时间间隔（假设为 1 秒）

    # 状态转移矩阵：包括位置、速度、姿态、角速度和加速度
    kf.F = np.array([
        [1, 0, 0, dt, 0, 0, 0.5 * dt**2, 0, 0, 0, 0, 0, 0, 0, 0],  # 经度状态
        [0, 1, 0, 0, dt, 0, 0, 0.5 * dt**2, 0, 0, 0, 0, 0, 0, 0],  # 纬度状态
        [0, 0, 1, 0, 0, dt, 0, 0, 0.5 * dt**2, 0, 0, 0, 0, 0, 0],  # 高度状态
        [0, 0, 0, 1, 0, 0, dt, 0, 0, 0, 0, 0, 0, 0, 0],  # 经度速度
        [0, 0, 0, 0, 1, 0, 0, dt, 0, 0, 0, 0, 0, 0, 0],  # 纬度速度
        [0, 0, 0, 0, 0, 1, 0, 0, dt, 0, 0, 0, 0, 0, 0],  # 高度速度
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 俯仰角
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # 滚转角
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # 偏航角
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # 俯仰角速度
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # 滚转角速度
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # 偏航角速度
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # 加速度x
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # 加速度y
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # 加速度z
    ])

    # 观测矩阵：包括GNSS位置和INS加速度
    kf.H = np.array([
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 观测经度
        [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 观测纬度
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 观测高度
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # 观测加速度x
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # 观测加速度y
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # 观测加速度z
    ])

    kf.P *= 500  # 初始协方差
    kf.R = np.diag([100, 100, 100, 5, 5, 5])  # 分别调整每个观测值的噪声方精度，纬度，高度，acc_x, acc_y, acc_z
    kf.Q = np.eye(15) * 0.01  # 过程噪声

    # 初始状态：经度、纬度、高度、速度、姿态、角速度、加速度
    kf.x = np.array(initial_state)  # 初始位置、速度、角度、角速度

    return kf
def integrate_gnss_ins_tight_coupling(merged_data):
    # 获取初始状态（可以选择用第一条数据）
    initial_state = [
        merged_data.iloc[0]["longitude"],
        merged_data.iloc[0]["latitude"],
        merged_data.iloc[0]["altitude"] if "altitude" in merged_data.columns else 0.0,
        0,  # 初始速度，假设为0
        0,  # 初始速度，假设为0
        0,  # 初始速度，假设为0
        0,  # 初始姿态，假设为0
        0,  # 初始姿态，假设为0
        0,  # 初始姿态，假设为0
        0,  # 初始角速度，假设为0
        0,  # 初始角速度，假设为0
        0,  # 初始角速度，假设为0
        0,  # 初始加速度x，假设为0
        0,  # 初始加速度y，假设为0
        0   # 初始加速度z，假设为0
    ]

    # 初始化卡尔曼滤波器
    kf = setup_kalman_filter_with_ins_gnss(initial_state)
    fused_positions = []

    # 进行数据融合
    for _, row in merged_data.iterrows():
        # GNSS 数据观测：提取经度、纬度和高度
        z_gnss = np.array([row["longitude"], row["latitude"], row["altitude"]])

        # INS 数据观测：提取加速度（假设加速度数据在row的"acc_x", "acc_y", "acc_z"列中）
        z_ins = np.array([row["acc_x"], row["acc_y"], row["acc_z"]])

        # 合并观测：将GNSS和INS数据合并，构成6维观测向量
        z = np.concatenate([z_gnss, z_ins])

        # 进行预测和更新
        kf.predict()
        kf.update(z)

        # 保存融合的结果（经度、纬度、高度）
        fused_positions.append(kf.x[:3])  # 只保留位置部分

    return np.array(fused_positions)



# 主函数
def main():
    gnss_df = load_gnss_data("../processed_bd.txt")
    ins_df = load_ins_data("../processed_gd.txt")

    # 过滤高度异常值
    gnss_clean, gnss_outliers = filter_altitude_outliers(gnss_df)

    # 数据对齐与融合
    merged_data = align_data(ins_df, gnss_clean, time_tolerance_sec=1)
    print(merged_data)
    fused_positions = integrate_gnss_ins_tight_coupling(merged_data)

    # 绘图
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    # GNSS正常点
    ax.scatter(gnss_clean["longitude"], gnss_clean["latitude"], gnss_clean["altitude"], label="GNSS Normal", color="r", s=10)

    # GNSS高度异常点
    ax.scatter(gnss_outliers["longitude"], gnss_outliers["latitude"], gnss_outliers["altitude"], label="GNSS Altitude Outliers", color="orange", s=20, marker='x')

    # 使用卡尔曼滤波的高度数据绘制平滑融合轨迹
    ax.plot(fused_positions[:, 0], fused_positions[:, 1], fused_positions[:, 2], label="Smoothed Fused", color="b",
            linewidth=2)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Altitude')
    ax.set_title("GNSS and INS Data Fusion with Altitude Outlier Filtering")
    ax.legend()
    plt.show()



if __name__ == "__main__":
    main()
