import re

# 文件路径
input_file = r"../bd.txt"
output_file = r"../processed_bd.txt"

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    segment = []  # 用于存储一段数据
    lines_processed = 0
    lines_written = 0

    for line in infile:
        lines_processed += 1

        # 空行表示段落结束
        if line.strip() == "":
            # 处理当前段落
            segment_data = "\n".join(segment)
            timestamp_match = re.search(r"\[(.*?)\]", segment_data)
            position_match = re.search(r"Position:\s*(.*?)'E\s*(.*?)'N", segment_data)
            altitude_match = re.search(r"Altitude:\s*(.*?)m", segment_data)

            if timestamp_match and position_match and altitude_match:
                timestamp = timestamp_match.group(1)
                longitude = position_match.group(1)
                latitude = position_match.group(2)
                altitude = altitude_match.group(1)
                # 写入输出文件
                outfile.write(f"{timestamp}, {longitude}'E, {latitude}'N, {altitude}m\n")
                lines_written += 1

            # 清空当前段
            segment = []
        else:
            segment.append(line.strip())  # 收集段内内容

    # 处理最后一段（避免遗漏）
    if segment:
        segment_data = "\n".join(segment)
        timestamp_match = re.search(r"\[(.*?)\]", segment_data)
        position_match = re.search(r"Position:\s*(.*?)'E\s*(.*?)'N", segment_data)
        altitude_match = re.search(r"Altitude:\s*(.*?)m", segment_data)

        if timestamp_match and position_match and altitude_match:
            timestamp = timestamp_match.group(1)
            longitude = position_match.group(1)
            latitude = position_match.group(2)
            altitude = altitude_match.group(1)
            outfile.write(f"{timestamp}, {longitude}°E, {latitude}°N, {altitude}m\n")
            lines_written += 1

print(f"处理完成：共处理了 {lines_processed} 行，提取并写入了 {lines_written} 行有效数据。结果已保存到 {output_file}。")
