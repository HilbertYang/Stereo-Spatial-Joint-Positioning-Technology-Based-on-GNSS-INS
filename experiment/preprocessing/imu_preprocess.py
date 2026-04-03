import re
import numpy as np

# 定义函数从文件中提取并格式化数据
def extract_and_format_data_with_correction(file_path, output_path, acc_bias, remove_gravity=True):
    def calibrate_acceleration(acc, acc_bias):
        """
        校正加速度数据，移除零偏。
        """
        return acc - acc_bias

    def transform_acceleration(acc, pitch, roll, yaw, remove_gravity=True):
        """
        将加速度从机体坐标系转换到ENU坐标系。
        """
        # Rotation matrices
        R_x = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ])
        R_y = np.array([
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)]
        ])
        R_z = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ])
        # Combined rotation matrix
        R_b2n = R_z @ R_y @ R_x

        # Transform acceleration
        acc_global = R_b2n @ acc

        # Optionally remove gravity
        if remove_gravity:
            g = 9.80665  # Gravity in m/s^2
            acc_global -= np.array([0, 0, g])

        return acc_global

    with open(file_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8') as outfile:
        segment = []

        for line in infile:
            # 收集段落内容
            if line.strip():
                segment.append(line.strip())
            else:
                # 处理段落
                if segment:
                    segment_data = "\n".join(segment)
                    timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]', segment_data)
                    data_match = re.search(r'RX：(.*)', segment_data)

                    if timestamp_match and data_match:
                        timestamp = timestamp_match.group(1)
                        data = data_match.group(1).strip()

                        # 提取字段数据
                        pit = float(re.search(r'pit:\s*([-\d\.]+)', data).group(1))
                        rol = float(re.search(r'rol:\s*([-\d\.]+)', data).group(1))
                        yaw = float(re.search(r'yaw:\s*([-\d\.]+)', data).group(1))
                        acc_x = float(re.search(r'acc_x:\s*([-\d\.]+)', data).group(1))
                        acc_y = float(re.search(r'acc_y:\s*([-\d\.]+)', data).group(1))
                        acc_z = float(re.search(r'acc_z:\s*([-\d\.]+)', data).group(1))
                        gyr_x = re.search(r'gyr_x:\s*([-\d\.]+)', data).group(1)
                        gyr_y = re.search(r'gyr_y:\s*([-\d\.]+)', data).group(1)
                        gyr_z = re.search(r'gyr_z:\s*([-\d\.]+)', data).group(1)

                        # 原始加速度
                        raw_acc = np.array([acc_x, acc_y, acc_z])

                        # 校正零偏
                        calibrated_acc = calibrate_acceleration(raw_acc, acc_bias)

                        # 转换到 ENU 坐标系
                        transformed_acc = transform_acceleration(calibrated_acc, np.radians(pit), np.radians(rol), np.radians(yaw), remove_gravity)

                        # 格式化处理后的数据
                        formatted_data = f"pit: {pit}, rol: {rol}, yaw: {yaw}, " \
                                        f"acc_x: {transformed_acc[0]:.3f}, acc_y: {transformed_acc[1]:.3f}, acc_z: {transformed_acc[2]:.3f}, " \
                                        f"gyr_x: {gyr_x}, gyr_y: {gyr_y}, gyr_z: {gyr_z}"

                        # 写入格式化结果
                        outfile.write(f"{timestamp}, {formatted_data}\n")

                    # 清空段落
                    segment = []

        print(f"数据处理完成，结果已保存到 {output_path}")

# 零偏参数（根据你的统计结果）
acc_bias = np.array([650, 800, 14258.2])

# 设置输入文件路径和输出文件路径
input_file = '../gd.txt'  # 输入文件路径
output_file = '../processed_gd.txt'  # 输出文件路径

# 调用函数进行数据提取、校正和格式化
extract_and_format_data_with_correction(input_file, output_file, acc_bias)
