import pandas as pd
import numpy as np

# 文件路径
file_path = 'target_corrected.txt'

# 读取数据并提取高度
data = []
lines = []
with open(file_path, 'r') as file:
    for line in file:
        lines.append(line)  # 保存原始行
        if 'm' in line:
            parts = line.split()
            try:
                altitude = float(parts[-2].replace('m', ''))
                data.append(altitude)
            except ValueError:
                data.append(None)  # 解析错误的行用None表示
        else:
            data.append(None)  # 非高度行用None表示

# 将高度数据转换为DataFrame并计算平滑高度
df = pd.DataFrame(data, columns=['altitude'])
window_size = 3
df['smoothed_altitude'] = df['altitude'].rolling(window=window_size, center=True).mean()

# 标记异常点
threshold = 100
df['is_anomaly'] = abs(df['altitude'] - df['smoothed_altitude']) > threshold

# 将非异常的行写回文件
with open(file_path, 'w') as file:
    idx = 0
    for line in lines:
        # 若该行高度不异常或没有高度数据，保留该行
        if df['is_anomaly'][idx] == False or df['altitude'][idx] is None:
            file.write(line)
        idx += 1
