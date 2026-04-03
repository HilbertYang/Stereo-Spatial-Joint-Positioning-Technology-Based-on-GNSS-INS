import re

# 定义函数从文件中提取并格式化数据
def extract_and_format_data(file_path, output_path):
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
                        pit = re.search(r'pit:\s*([-\d\.]+)', data)
                        rol = re.search(r'rol:\s*([-\d\.]+)', data)
                        yaw = re.search(r'yaw:\s*([-\d\.]+)', data)
                        acc_x = re.search(r'acc_x:\s*([-\d\.]+)', data)
                        acc_y = re.search(r'acc_y:\s*([-\d\.]+)', data)
                        acc_z = re.search(r'acc_z:\s*([-\d\.]+)', data)
                        gyr_x = re.search(r'gyr_x:\s*([-\d\.]+)', data)
                        gyr_y = re.search(r'gyr_y:\s*([-\d\.]+)', data)
                        gyr_z = re.search(r'gyr_z:\s*([-\d\.]+)', data)

                        # 格式化提取的数据
                        formatted_data = f"pit: {pit.group(1) if pit else 'N/A'}, rol: {rol.group(1) if rol else 'N/A'}, yaw: {yaw.group(1) if yaw else 'N/A'}, " \
                                        f"acc_x: {acc_x.group(1) if acc_x else 'N/A'}, acc_y: {acc_y.group(1) if acc_y else 'N/A'}, acc_z: {acc_z.group(1) if acc_z else 'N/A'}, " \
                                        f"gyr_x: {gyr_x.group(1) if gyr_x else 'N/A'}, gyr_y: {gyr_y.group(1) if gyr_y else 'N/A'}, gyr_z: {gyr_z.group(1) if gyr_z else 'N/A'}"

                        # 写入格式化结果
                        outfile.write(f"{timestamp}, {formatted_data}\n")

                    # 清空段落
                    segment = []

        # 处理最后段落（避免遗漏）
        if segment:
            segment_data = "\n".join(segment)
            timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]', segment_data)
            data_match = re.search(r'RX：(.*)', segment_data)

            if timestamp_match and data_match:
                timestamp = timestamp_match.group(1)
                data = data_match.group(1).strip()

                # 提取字段数据
                pit = re.search(r'pit:\s*([-\d\.]+)', data)
                rol = re.search(r'rol:\s*([-\d\.]+)', data)
                yaw = re.search(r'yaw:\s*([-\d\.]+)', data)
                acc_x = re.search(r'acc_x:\s*([-\d\.]+)', data)
                acc_y = re.search(r'acc_y:\s*([-\d\.]+)', data)
                acc_z = re.search(r'acc_z:\s*([-\d\.]+)', data)
                gyr_x = re.search(r'gyr_x:\s*([-\d\.]+)', data)
                gyr_y = re.search(r'gyr_y:\s*([-\d\.]+)', data)
                gyr_z = re.search(r'gyr_z:\s*([-\d\.]+)', data)

                # 格式化提取的数据
                formatted_data = f"pit: {pit.group(1) if pit else 'N/A'}, rol: {rol.group(1) if rol else 'N/A'}, yaw: {yaw.group(1) if yaw else 'N/A'}, " \
                                f"acc_x: {acc_x.group(1) if acc_x else 'N/A'}, acc_y: {acc_y.group(1) if acc_y else 'N/A'}, acc_z: {acc_z.group(1) if acc_z else 'N/A'}, " \
                                f"gyr_x: {gyr_x.group(1) if gyr_x else 'N/A'}, gyr_y: {gyr_y.group(1) if gyr_y else 'N/A'}, gyr_z: {gyr_z.group(1) if gyr_z else 'N/A'}"

                # 写入格式化结果
                outfile.write(f"{timestamp}, {formatted_data}\n")

    print(f"数据处理完成，结果已保存到 {output_path}")

# 设置输入文件路径和输出文件路径
input_file = '../2024_12_19_gd_new.txt'  # 输入文件路径
output_file = '../2024_12_19_gd_new_processed.txt'  # 输出文件路径

# 调用函数进行数据提取和格式化
extract_and_format_data(input_file, output_file)