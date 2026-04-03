import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import re

# 读取数据文件并解析
def read_data(filename):
    timestamps = []
    acc_x = []
    acc_y = []
    acc_z = []

    # 使用正则表达式解析文件中的每一行
    with open(filename, 'r') as file:
        for line in file:
            # 提取加速度数据和时间戳
            match = re.match(r'([0-9\-:\. ]+), .*acc_x:\s*(-?\d+), acc_y:\s*(-?\d+), acc_z:\s*(-?\d+)', line)
            if match:
                timestamps.append(match.group(1))
                acc_x.append(int(match.group(2)))  # 或者使用 float()
                acc_y.append(int(match.group(3)))
                acc_z.append(int(match.group(4)))

    return np.array(timestamps), np.array(acc_x), np.array(acc_y), np.array(acc_z)

# 文件路径
filename = '../2024_12_19_gd_processed.txt'

# 读取数据
timestamps, acc_x, acc_y, acc_z = read_data(filename)

# 去除零偏
zero_offset_x = 1006  # acc_x 的零偏
zero_offset_y = 878   # acc_y 的零偏
zero_offset_z = 14324 # acc_z 的零偏

# 减去零偏
acc_x -= zero_offset_x
acc_y -= zero_offset_y
acc_z -= zero_offset_z

# 将时间戳转为时间差
time_diffs = []
for i in range(1, len(timestamps)):
    prev_time = np.datetime64(timestamps[i-1], 'ms')
    curr_time = np.datetime64(timestamps[i], 'ms')
    time_diffs.append((curr_time - prev_time) / np.timedelta64(1, 's'))
time_diffs.insert(0, time_diffs[0])  # 为了使得初始时间差也能参与计算

# 数值积分计算速度
dt = np.array(time_diffs)
velocity_x = np.cumsum(acc_x * dt)
velocity_y = np.cumsum(acc_y * dt)
velocity_z = np.cumsum(acc_z * dt)

# 数值积分计算位置
position_x = np.cumsum(velocity_x * dt)
position_y = np.cumsum(velocity_y * dt)
position_z = np.cumsum(velocity_z * dt)

# 绘制三维轨迹图
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot(position_x, position_y, position_z, label='Motion Trajectory')

ax.set_xlabel('X Position (m)')
ax.set_ylabel('Y Position (m)')
ax.set_zlabel('Z Position (m)')
ax.set_title('3D Motion Trajectory')

plt.show()
