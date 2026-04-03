import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 读取文件并解析数据
data = []

with open('../processed_bd.txt', 'r') as file:
    for line in file:
        # 移除行尾换行符并分割
        line = line.strip()

        # 解析每一行数据
        parts = line.split(', ')

        # 时间、经度、纬度、海拔信息
        time = parts[0]
        longitude = float(parts[1].replace("'E", ""))  # 去掉经度的引号
        latitude = float(parts[2].replace("'N", ""))  # 去掉纬度的引号
        altitude = float(parts[3].replace('m', ''))  # 去掉海拔的单位

        data.append((time, longitude, latitude, altitude))

# 创建 DataFrame
df = pd.DataFrame(data, columns=["Time", "Longitude", "Latitude", "Altitude"])

# 将时间列转换为 datetime 类型
df["Time"] = pd.to_datetime(df["Time"])

# 创建三维图形
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 绘制三维数据：经度（Longitude）、纬度（Latitude）作为 X 和 Y 坐标，海拔（Altitude）作为 Z 坐标
scatter = ax.scatter(df["Longitude"], df["Latitude"], df["Altitude"], c=df["Altitude"], cmap='viridis', s=50)

# 设置标签
ax.set_xlabel('Longitude (°E)')
ax.set_ylabel('Latitude (°N)')
ax.set_zlabel('Altitude (m)')

# 设置标题
ax.set_title('3D Scatter Plot of Longitude, Latitude, and Altitude')

# 添加颜色条（显示海拔高度的颜色映射）
fig.colorbar(scatter, label='Altitude (m)')

# 显示图形
plt.show()
