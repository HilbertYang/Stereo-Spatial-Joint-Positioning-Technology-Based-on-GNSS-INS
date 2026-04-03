import pandas as pd

# 读取数据文件
with open('target_corrected.txt', 'r') as file:
    lines = file.readlines()

# 初始化数据列表
data = {
    'lat': [],
    'lon': [],
    'alt': [],
    'pit': [],
    'rol': [],
    'yaw': [],
    'acc_x': [],
    'acc_y': [],
    'acc_z': [],
    'gyr_x': [],
    'gyr_y': [],
    'gyr_z': []
}

# 解析数据
for i in range(0, len(lines), 2):
    imu_data = lines[i].strip()
    gps_data = lines[i + 1].strip()

    imu_parts = imu_data.split(',')
    gps_parts = gps_data.split(' ')

    try:
        data['pit'].append(float(imu_parts[0].split(': ')[1]))
        data['rol'].append(float(imu_parts[1].split(': ')[1]))
        data['yaw'].append(float(imu_parts[2].split(': ')[1]))
        data['acc_x'].append(float(imu_parts[3].split(': ')[1]))
        data['acc_y'].append(float(imu_parts[4].split(': ')[1]))
        data['acc_z'].append(float(imu_parts[5].split(': ')[1]))
        data['gyr_x'].append(float(imu_parts[6].split(': ')[1]))
        data['gyr_y'].append(float(imu_parts[7].split(': ')[1]))
        data['gyr_z'].append(float(imu_parts[8].split(': ')[1]))

        lon = float(gps_parts[0].strip('E').replace("'", ""))
        lat = float(gps_parts[1].strip('N').replace("'", ""))
        alt = float(gps_parts[2].strip('m'))

        data['lon'].append(lon)
        data['lat'].append(lat)
        data['alt'].append(alt)
    except ValueError as e:
        print(f"Error parsing line {i // 2 + 1}: {e}")
        continue

# 创建 DataFrame 并保存为 Excel 文件
df = pd.DataFrame(data)
df.to_excel('processed_data.xlsx', index=False)
