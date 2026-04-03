import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 打开文件并读取内容
with open('target_corrected.txt', 'r') as file:
    data = file.readlines()

# 提取经纬度和高度数据
lats, longs, alts = [], [], []
for line in data:
    if 'E' in line and 'N' in line:
        try:
            # 分割经纬度和高度字符串
            parts = line.strip().split(' ')
            long_str, lat_str, alt_str = parts[0], parts[1], parts[2].replace("m", "")
            # 去掉度符号并转换为浮点数
            long_val = float(long_str.replace("E", "").replace("'", ""))
            lat_val = float(lat_str.replace("N", "").replace("'", ""))
            alt_val = float(alt_str)
            longs.append(long_val)
            lats.append(lat_val)
            alts.append(alt_val)
        except ValueError:
            # 跳过无法解析的行
            continue

# 绘制3D散点图
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(longs, lats, alts, c=alts, cmap='viridis', marker='o')

# 添加坐标轴标签
ax.set_title('3D BDS Scatter Plot')
ax.set_xlabel('Longitude (°E)')
ax.set_ylabel('Latitude (°N)')
ax.set_zlabel('Altitude (m)')

# # 添加颜色条
# plt.colorbar(sc, label='Altitude (m)')
plt.show()
