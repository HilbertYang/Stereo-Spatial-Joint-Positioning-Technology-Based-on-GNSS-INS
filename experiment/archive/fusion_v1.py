import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import re
from filterpy.kalman import KalmanFilter


def parse_timestamp(line):
    # 例如：2024-12-13 21:15:14.420, 121.20766°E, 31.5929°N, 13.5m
    match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", line)
    if match:
        return match.group(0)
    return None
def load_gnss_data(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            # print(f"Processing line: {line}")  # 打印每行内容，帮助调试
            if "'E" in line and "'N" in line:  # 查找经度和纬度
                timestamp = parse_timestamp(line)
                if timestamp:
                    parts = line.split(",")  # 按逗号分割
                    try:
                        # 提取经度、纬度和海拔
                        longitude = float(re.sub(r"'E", "", parts[1].strip()))  # 去除经度的单位
                        latitude = float(re.sub(r"'N", "", parts[2].strip()))  # 去除纬度的单位
                        altitude = float(re.sub(r"m", "", parts[3].strip()))  # 提取海拔并去除单位
                        data.append([timestamp, longitude, latitude, altitude])
                    except (IndexError, ValueError) as e:
                        print(f"Error parsing line: {line} ({e})")
                        continue

    gnss_df = pd.DataFrame(data, columns=["timestamp", "longitude", "latitude", "altitude"])
    gnss_df["timestamp"] = pd.to_datetime(gnss_df["timestamp"])  # 强制转换为 datetime 类型
    print(f"Loaded GNSS data: {len(gnss_df)} rows")  # 打印加载的GNSS数据的行数
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
                        gyr_x = float(parts[7].split(":")[1].strip())
                        gyr_y = float(parts[8].split(":")[1].strip())
                        gyr_z = float(parts[9].split(":")[1].strip())
                        data.append([timestamp, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z])
                    except IndexError:
                        print(f"Skipping line due to missing data: {line}")
                        continue
    ins_df = pd.DataFrame(data, columns=["timestamp", "acc_x", "acc_y", "acc_z", "gyr_x", "gyr_y", "gyr_z"])
    ins_df["timestamp"] = pd.to_datetime(ins_df["timestamp"])  # 强制转换为 datetime 类型

    # 平滑加速度数据
    ins_df["acc_x"] = ins_df["acc_x"].rolling(window=5, center=True).mean()
    ins_df["acc_y"] = ins_df["acc_y"].rolling(window=5, center=True).mean()
    ins_df["acc_z"] = ins_df["acc_z"].rolling(window=5, center=True).mean()

    print(f"Loaded INS data: {len(ins_df)} rows")
    return ins_df


# 对齐GNSS和INS数据
def align_data(gnss_df, ins_df):
    # 将时间戳对齐到最近的GNSS数据点
    merged_data = pd.merge_asof(gnss_df.sort_values("timestamp"), ins_df.sort_values("timestamp"), on="timestamp",
                                tolerance=pd.Timedelta('1s'))
    print(f"Merged data shape: {merged_data.shape}")  # 打印合并后的数据
    return merged_data


# 设置卡尔曼滤波器
def setup_kalman_filter(initial_state):
    kf = KalmanFilter(dim_x=4, dim_z=2)
    dt = 1  # 假设采样间隔为1秒

    kf.F = np.array([[1, 0, dt, 0],
                     [0, 1, 0, dt],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])

    kf.H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]])

    kf.P *= 500  # 初始协方差
    kf.R = np.eye(2) * 10  # 观测噪声
    kf.Q = np.eye(4) * 0.1  # 过程噪声

    # 使用 GNSS 数据的初始位置作为初始状态
    kf.x = np.array([initial_state[0], initial_state[1], 0, 0])  # [x, y, vx, vy]
    return kf


def integrate_gnss_ins(merged_data):
    # 获取 GNSS 数据的初始位置
    initial_state = merged_data.iloc[0][["longitude", "latitude"]].values
    kf = setup_kalman_filter(initial_state)  # 传入初始状态

    fused_positions = []

    for _, row in merged_data.iterrows():
        # GNSS观测
        z = np.array([row["longitude"], row["latitude"]])

        # INS预测（简单利用加速度）
        acc_x = row["acc_x"]
        acc_y = row["acc_y"]

        # 如果加速度为 NaN，则设置默认值
        if np.isnan(acc_x):
            acc_x = 0.0
        if np.isnan(acc_y):
            acc_y = 0.0

        # 更新卡尔曼滤波器状态转移矩阵
        kf.F[2, 2] += acc_x * 0.1  # 假设0.1为加速度的权重
        kf.F[3, 3] += acc_y * 0.1

        # 卡尔曼滤波器预测和更新
        kf.predict()
        kf.update(z)

        # 保存位置 (x, y)
        fused_positions.append(kf.x[:2])

    fused_positions = np.array(fused_positions)
    print(f"Shape of fused_positions after fusion: {fused_positions.shape}")
    return fused_positions


def remove_outliers(df):
    # 计算经度、纬度、海拔的统计信息
    desc = df[["longitude", "latitude", "altitude"]].describe()
    print("Data statistics:\n", desc)

    # 设置范围阈值 (3倍标准差)
    lon_mean, lon_std = desc.loc["mean", "longitude"], desc.loc["std", "longitude"]
    lat_mean, lat_std = desc.loc["mean", "latitude"], desc.loc["std", "latitude"]
    alt_mean, alt_std = desc.loc["mean", "altitude"], desc.loc["std", "altitude"]

    # 定义异常点的条件
    condition = (
        (df["longitude"] > lon_mean - 3 * lon_std) & (df["longitude"] < lon_mean + 3 * lon_std) &
        (df["latitude"] > lat_mean - 3 * lat_std) & (df["latitude"] < lat_mean + 3 * lat_std) &
        (df["altitude"] > alt_mean - 3 * alt_std) & (df["altitude"] < alt_mean + 3 * alt_std)
    )

    # 筛选出正常数据
    cleaned_df = df[condition]
    print(f"Removed {len(df) - len(cleaned_df)} outliers")
    return cleaned_df
# 主函数
def main():
    # 加载数据
    gnss_df = load_gnss_data("../processed_bd.txt")
    ins_df = load_ins_data("../processed_gd.txt")

    if gnss_df.shape[0] == 0:
        print("No GNSS data loaded. Exiting.")
        return

    # 剔除GNSS数据的异常点
    gnss_df = remove_outliers(gnss_df)

    # 对齐数据
    merged_data = align_data(gnss_df, ins_df)

    # 数据融合
    fused_positions = integrate_gnss_ins(merged_data)

    if fused_positions.shape[0] > 0:
        # 绘制三维图
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection='3d')

        # 绘制 GNSS 数据
        ax.scatter(gnss_df["longitude"], gnss_df["latitude"], gnss_df["altitude"], label="GNSS", color="r")

        # 绘制融合后的数据
        ax.scatter(fused_positions[:, 0], fused_positions[:, 1], gnss_df["altitude"][:len(fused_positions)], label="Fused", color="b")

        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_zlabel('Altitude')
        ax.set_title("GNSS and INS Data Fusion in 3D")
        ax.legend()
        plt.show()
    else:
        print("No fused positions to plot.")

if __name__ == "__main__":
    main()