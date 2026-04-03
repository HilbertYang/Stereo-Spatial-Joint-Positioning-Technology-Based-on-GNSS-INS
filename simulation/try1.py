import pandas as pd
import matplotlib.pyplot as plt
import re
from mpl_toolkits.mplot3d import Axes3D

# 读取文件
file_path = 'target_corrected.txt'

with open(file_path, 'r', encoding='utf-8') as file:
    data = file.read()

# 解析数据
pattern = re.compile(
    r'pit: ([\d\.\-]+), rol: ([\d\.\-]+), yaw: ([\d\.\-]+), acc_x: ([\d\.\-]+), acc_y: ([\d\.\-]+), acc_z: ([\d\.\-]+), gyr_x: ([\d\.\-]+), gyr_y: ([\d\.\-]+), gyr_z: ([\d\.\-]+), temp: ([\d\.\-]+)\n([\d\.]+)\'E ([\d\.]+)\'N ([\d\.\-]+)m ([\d\.]+)Km/H')

matches = pattern.findall(data)
parsed_data = []

for match in matches:
    # 处理高度字段，去除无效的字符
    altitude_str = match[12]
    try:
        altitude = float(altitude_str)
    except ValueError:
        altitude = None  # 无法转换为浮点数时设置为None或其他合适的默认值

    # 处理经度和纬度字段，去除无效的字符
    longitude_str = match[10]
    latitude_str = match[11]

    try:
        longitude = float(longitude_str)
        latitude = float(latitude_str)
    except ValueError:
        longitude = None
        latitude = None

    parsed_data.append({
        'pit': float(match[0]),
        'rol': float(match[1]),
        'yaw': float(match[2]),
        'acc_x': float(match[3]),
        'acc_y': float(match[4]),
        'acc_z': float(match[5]),
        'gyr_x': float(match[6]),
        'gyr_y': float(match[7]),
        'gyr_z': float(match[8]),
        'temp': float(match[9]),
        'longitude': longitude,
        'latitude': latitude,
        'altitude': altitude,
        'speed': match[13]
    })

# 创建 DataFrame
df = pd.DataFrame(parsed_data)

# 过滤掉无效数据点
df = df.dropna(subset=['longitude', 'latitude', 'altitude'])

# 绘制3D图表
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

sc = ax.scatter(df['longitude'], df['latitude'], df['altitude'], c=df['altitude'], cmap='viridis')
plt.colorbar(sc, label='Altitude (m)')

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_zlabel('Altitude (m)')

plt.show()
