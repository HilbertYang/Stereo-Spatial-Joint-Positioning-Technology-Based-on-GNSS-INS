import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 读取1.txt文件
with open('../bd.txt', 'r') as file:
    lines = file.readlines()

# 定义正则表达式提取经纬度和海拔
lat_pattern = re.compile(r"Position: (\d+\.\d+)'E (\d+\.\d+)'N")
altitude_pattern = re.compile(r"Altitude: (\d+\.\d+)m")

# 用来存储经度、纬度和海拔数据
longitudes = []
latitudes = []
altitudes = []

# 遍历文件行提取数据
for line in lines:
    # 提取经纬度
    lat_match = lat_pattern.search(line)
    if lat_match:
        longitude = float(lat_match.group(1))  # 经度
        latitude = float(lat_match.group(2))  # 纬度
        longitudes.append(longitude)
        latitudes.append(latitude)

    # 提取海拔数据
    altitude_match = altitude_pattern.search(line)
    if altitude_match:
        altitude = float(altitude_match.group(1))  # 海拔
        altitudes.append(altitude)

# 检查数据长度
print(f"Number of longitude entries: {len(longitudes)}")
print(f"Number of latitude entries: {len(latitudes)}")
print(f"Number of altitude entries: {len(altitudes)}")

# 确保经纬度和海拔数据的长度一致
min_length = min(len(longitudes), len(latitudes), len(altitudes))
longitudes = longitudes[:min_length]
latitudes = latitudes[:min_length]
altitudes = altitudes[:min_length]

# 将数据转换为numpy数组以便处理
longitudes = np.array(longitudes)
latitudes = np.array(latitudes)
altitudes = np.array(altitudes)

# 创建3D图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制3D路线
ax.plot(longitudes, latitudes, altitudes, label='3D Route', color='b', marker='o')

# 设置图形标签
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_zlabel('Altitude (m)')

# 设置标题
ax.set_title('3D Route Based on BDS Data')

# 显示图例
ax.legend()

# 显示图形
plt.show()
