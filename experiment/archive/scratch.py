import pandas as pd
import numpy as np
import re
from datetime import timedelta


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


# 主程序
def main():
    # 加载数据
    ins_df = load_ins_data('../processed_gd.txt')
    gnss_df = load_gnss_data('../processed_bd.txt')

    # 对齐数据
    aligned_df = align_data(ins_df, gnss_df, time_tolerance_sec=1)

    # 输出对齐后的数据
    print(f"对齐后的数据条数: {len(aligned_df)}")
    print(aligned_df)  # 打印前几行查看对齐情况


if __name__ == "__main__":
    main()