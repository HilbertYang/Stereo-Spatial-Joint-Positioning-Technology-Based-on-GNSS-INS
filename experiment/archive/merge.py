import pandas as pd
import re

def align_data_with_interpolation(gnss_df, ins_df):
    # 对GNSS和INS数据按照时间戳排序
    gnss_df = gnss_df.sort_values(by="timestamp")
    ins_df = ins_df.sort_values(by="timestamp")

    # 使用线性插值将INS数据对齐到GNSS的时间戳上
    ins_df.set_index('timestamp', inplace=True)
    ins_df_interpolated = ins_df.reindex(gnss_df['timestamp']).interpolate(method='linear')

    # 合并GNSS数据和插值后的INS数据
    merged_data = pd.concat([gnss_df.reset_index(drop=True), ins_df_interpolated.reset_index(drop=True)], axis=1)

    return merged_data


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

def main():
    gnss_df = load_gnss_data("../processed_bd.txt")
    ins_df = load_ins_data("../processed_gd.txt")

    # 数据对齐与融合
    merged_data = align_data_with_interpolation(gnss_df, ins_df)
    print(merged_data)

if __name__ == '__main__':
    main()