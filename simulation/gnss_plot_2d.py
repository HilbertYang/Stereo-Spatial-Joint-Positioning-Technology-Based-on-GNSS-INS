import matplotlib.pyplot as plt

# 打开文件并读取内容
with open('target_corrected.txt', 'r') as file:
    data = file.readlines()

# 提取经纬度数据
lats, longs = [], []
for line in data:
    if 'E' in line and 'N' in line:
        try:
            # 分割经纬度字符串
            long_str, lat_str = line.strip().split(' ')[0], line.strip().split(' ')[1]
            # 去掉度符号并转换为浮点数
            long_val = float(long_str.replace("E", "").replace("'", ""))
            lat_val = float(lat_str.replace("N", "").replace("'", ""))
            longs.append(long_val)
            lats.append(lat_val)
        except ValueError:
            # 跳过无法解析的行
            continue

# 绘制散点图
plt.figure(figsize=(10, 6))
plt.scatter(longs, lats, c='blue', marker='o')
plt.title('BDS Scatter Plot')
plt.xlabel('Longitude (°E)')
plt.ylabel('Latitude (°N)')
plt.grid(True)
plt.show()
