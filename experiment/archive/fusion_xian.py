import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
from filterpy.kalman import KalmanFilter


# 解析时间戳
def parse_timestamp(line):
    match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line)
    return match.group(0) if match else None


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
            if "acc_x" in line:
                timestamp = parse_timestamp(line)
                if timestamp:
                    parts = line.split(", ")
                    try:
                        acc_x = float(parts[4].split(":")[1].strip())
                        acc_y = float(parts[5].split(":")[1].strip())
                        acc_z = float(parts[6].split(":")[1].strip())
                        data.append([timestamp, acc_x, acc_y, acc_z])
                    except IndexError:
                        continue
    ins_df = pd.DataFrame(data, columns=["timestamp", "acc_x", "acc_y", "acc_z"])
    ins_df["timestamp"] = pd.to_datetime(ins_df["timestamp"])
    return ins_df


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


# 对齐数据
def align_data(gnss_df, ins_df):
    aligned_data = pd.merge_asof(gnss_df.sort_values("timestamp"), ins_df.sort_values("timestamp"), on="timestamp",
                                 tolerance=pd.Timedelta('1s'))
    print(aligned_data)
    return aligned_data


# 设置卡尔曼滤波器
def setup_kalman_filter_with_altitude(initial_state):
    kf = KalmanFilter(dim_x=9, dim_z=3)  # 9维状态，3维观测（经度、纬度、高度）
    dt = 1  # 时间间隔

    # 状态转移矩阵：经度、纬度和高度的速度和加速度
    kf.F = np.array([[1, 0, 0, dt, 0, 0, 0.5 * dt ** 2, 0, 0],  # 位置
                     [0, 1, 0, 0, dt, 0, 0, 0.5 * dt ** 2, 0],
                     [0, 0, 1, 0, 0, dt, 0, 0, 0.5 * dt ** 2],
                     [0, 0, 0, 1, 0, 0, dt, 0, 0],  # 速度
                     [0, 0, 0, 0, 1, 0, 0, dt, 0],
                     [0, 0, 0, 0, 0, 1, 0, 0, dt],
                     [0, 0, 0, 0, 0, 0, 1, 0, 0],  # 加速度
                     [0, 0, 0, 0, 0, 0, 0, 1, 0],
                     [0, 0, 0, 0, 0, 0, 0, 0, 1]])

    # 观测矩阵：观测经度、纬度和高度
    kf.H = np.array([[1, 0, 0, 0, 0, 0, 0, 0, 0],
                     [0, 1, 0, 0, 0, 0, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0, 0, 0, 0]])

    kf.P *= 500  # 初始协方差
    kf.R = np.eye(3) * 10  # 观测噪声
    kf.Q = np.eye(9) * 0.1  # 过程噪声

    # 初始状态：经度、纬度和高度
    kf.x = np.array([initial_state[0], initial_state[1], initial_state[2], 0, 0, 0, 0, 0, 0])
    return kf


# 数据融合
def integrate_gnss_ins(merged_data):
    # 检查高度信息，加入默认高度 0
    initial_state = [
        merged_data.iloc[0]["longitude"],
        merged_data.iloc[0]["latitude"],
        merged_data.iloc[0]["altitude"] if "altitude" in merged_data.columns else 0.0
    ]

    kf = setup_kalman_filter_with_altitude(initial_state)  # 初始化卡尔曼滤波器
    fused_positions = []

    for _, row in merged_data.iterrows():
        # GNSS观测值包括经度、纬度和高度
        z = np.array([
            row["longitude"],
            row["latitude"],
            row["altitude"] if not np.isnan(row["altitude"]) else 0.0
        ])

        # 卡尔曼滤波器预测和更新
        kf.predict()
        kf.update(z)

        # 保存位置 (经度, 纬度, 高度)
        fused_positions.append(kf.x[:3])

    return np.array(fused_positions)


# 绘制GNSS和INS数据融合图
def plot_gnss_ins_fusion(gnss_clean, gnss_outliers, fused_positions):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    # GNSS正常点
    ax.scatter(gnss_clean["longitude"], gnss_clean["latitude"], gnss_clean["altitude"],
               label="GNSS Normal", color="r", s=10)

    # GNSS高度异常点
    ax.scatter(gnss_outliers["longitude"], gnss_outliers["latitude"], gnss_outliers["altitude"],
               label="GNSS Altitude Outliers", color="orange", s=20, marker='x')

    # 平滑融合轨迹
    ax.plot(fused_positions[:, 0], fused_positions[:, 1], gnss_clean["altitude"][:len(fused_positions)],
            label="Smoothed Fused", color="b", linewidth=2)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Altitude')
    ax.set_title("GNSS and INS Data Fusion with Altitude Outlier Filtering")
    ax.legend()
    plt.show()


# 主函数
def main():
    gnss_df = load_gnss_data("../processed_bd.txt")
    ins_df = load_ins_data("../processed_gd.txt")

    # 过滤高度异常值
    gnss_clean, gnss_outliers = filter_altitude_outliers(gnss_df)

    # 数据对齐与融合
    merged_data = align_data(gnss_clean, ins_df)
    fused_positions = integrate_gnss_ins(merged_data)

    # 绘制图表
    plot_gnss_ins_fusion(gnss_clean, gnss_outliers, fused_positions)


if __name__ == "__main__":
    main()
