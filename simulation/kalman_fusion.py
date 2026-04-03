import numpy as np
import matplotlib.pyplot as plt
from filterpy.kalman import KalmanFilter
from geographiclib.geodesic import Geodesic

# 设置地理转换
geod = Geodesic.WGS84


# 读取数据
def parse_data(file_path):
    gps_data = []
    imu_data = []

    with open(file_path, 'r') as file:
        for line in file:
            if 'E' in line:
                # 解析GPS数据
                parts = line.split()
                lon = float(parts[0].replace('E', '').replace("'", ""))
                lat = float(parts[1].replace('N', '').replace("'", ""))
                alt = float(parts[2].replace('m', '').replace("'", ""))
                gps_data.append((lat, lon, alt))
            elif 'pit' in line:
                # 解析IMU数据
                parts = line.split(',')
                pitch = float(parts[0].split(':')[1])
                roll = float(parts[1].split(':')[1])
                yaw = float(parts[2].split(':')[1])
                acc_x = int(parts[3].split(':')[1])
                acc_y = int(parts[4].split(':')[1])
                acc_z = int(parts[5].split(':')[1])
                imu_data.append((pitch, roll, yaw, acc_x, acc_y, acc_z))

    return gps_data, imu_data


# 将GPS数据转换为笛卡尔坐标
def gps_to_cartesian(gps_data, origin):
    cartesian_data = []
    for lat, lon, alt in gps_data:
        g = geod.Inverse(origin[0], origin[1], lat, lon)
        x = g['s12'] * np.cos(np.radians(g['azi1']))
        y = g['s12'] * np.sin(np.radians(g['azi1']))
        z = alt - origin[2]
        cartesian_data.append((x, y, z))
    return np.array(cartesian_data)


# 初始化卡尔曼滤波器
def initialize_kalman():
    kf = KalmanFilter(dim_x=6, dim_z=3)
    kf.x = np.zeros(6)  # 初始状态
    kf.F = np.array([[1, 0, 0, 1, 0, 0],
                     [0, 1, 0, 0, 1, 0],
                     [0, 0, 1, 0, 0, 1],
                     [0, 0, 0, 1, 0, 0],
                     [0, 0, 0, 0, 1, 0],
                     [0, 0, 0, 0, 0, 1]])  # 状态转移矩阵
    kf.H = np.array([[1, 0, 0, 0, 0, 0],
                     [0, 1, 0, 0, 0, 0],
                     [0, 0, 1, 0, 0, 0]])  # 测量矩阵
    kf.P *= 1000  # 初始协方差
    kf.R = np.eye(3) * 5  # 测量噪声
    kf.Q = np.eye(6) * 0.1  # 过程噪声
    return kf


# 主函数
def main():
    file_path = 'sample4.txt'
    gps_data, imu_data = parse_data(file_path)

    # 将第一条GPS数据作为原点
    origin = gps_data[0]
    cartesian_gps_data = gps_to_cartesian(gps_data, origin)

    # 初始化卡尔曼滤波器
    kf = initialize_kalman()

    # 存储融合结果和误差
    fused_positions = []
    errors_total = []
    errors_x = []
    errors_y = []
    errors_z = []

    for i in range(len(cartesian_gps_data)):
        gps_pos = cartesian_gps_data[i]

        # 使用加速度数据作为过程模型更新
        if i < len(imu_data):
            acc = imu_data[i][3:6]
            dt = 1  # 假设每次测量间隔为1秒
            kf.predict(u=acc)

        # 使用GPS数据更新测量
        kf.update(gps_pos)

        # 存储融合位置
        fused_pos = kf.x[:3].copy()
        fused_positions.append(fused_pos)

        # 计算融合前后的误差
        error_total = np.linalg.norm(gps_pos - fused_pos)  # 总误差
        error_x = abs(gps_pos[0] - fused_pos[0])  # 经度误差
        error_y = abs(gps_pos[1] - fused_pos[1])  # 纬度误差
        error_z = abs(gps_pos[2] - fused_pos[2])  # 高度误差

        # 存储误差
        errors_total.append(error_total)
        errors_x.append(error_x)
        errors_y.append(error_y)
        errors_z.append(error_z)

    fused_positions = np.array(fused_positions)

    # 绘制路径图
    fig1 = plt.figure()
    ax = fig1.add_subplot(111, projection='3d')
    ax.plot(fused_positions[:, 0], fused_positions[:, 1], fused_positions[:, 2], label='Fused Path')
    ax.scatter(cartesian_gps_data[:, 0], cartesian_gps_data[:, 1], cartesian_gps_data[:, 2], color='r', s=5,
               label='GPS Path')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.legend()
    ax.set_title('3D Fused and BDS Path')
    plt.show()

    # 绘制误差图
    fig2 = plt.figure()
    plt.plot(errors_total, label='Total Error')
    plt.xlabel('Time Step')
    plt.ylabel('Error (m)')
    plt.title('Total Fusion Error Over Time')
    plt.legend()
    plt.show()

    # 绘制各方向上的误差
    fig3 = plt.figure()
    plt.plot(errors_x, label='Longitude Error')
    plt.xlabel('Time Step')
    plt.ylabel('Error (m)')
    plt.title('Longitude Error Over Time')
    plt.legend()
    plt.show()

    fig4 = plt.figure()
    plt.plot(errors_y, label='Latitude Error')
    plt.xlabel('Time Step')
    plt.ylabel('Error (m)')
    plt.title('Latitude Error Over Time')
    plt.legend()
    plt.show()

    fig5 = plt.figure()
    plt.plot(errors_z, label='Altitude Error')
    plt.xlabel('Time Step')
    plt.ylabel('Error (m)')
    plt.title('Altitude Error Over Time')
    plt.legend()
    plt.show()

    # 计算误差的统计特征
    error_stats = {
        'total': {'mean': np.mean(errors_total), 'std': np.std(errors_total), 'max': np.max(errors_total),
                  'min': np.min(errors_total)},
        'x': {'mean': np.mean(errors_x), 'std': np.std(errors_x), 'max': np.max(errors_x), 'min': np.min(errors_x)},
        'y': {'mean': np.mean(errors_y), 'std': np.std(errors_y), 'max': np.max(errors_y), 'min': np.min(errors_y)},
        'z': {'mean': np.mean(errors_z), 'std': np.std(errors_z), 'max': np.max(errors_z), 'min': np.min(errors_z)}
    }

    print("Error statistics:")
    for axis in error_stats:
        print(
            f"{axis} - mean: {error_stats[axis]['mean']:.3f}, std: {error_stats[axis]['std']:.3f}, max: {error_stats[axis]['max']:.3f}, min: {error_stats[axis]['min']:.3f}")

    # 绘制误差直方图
    fig6 = plt.figure()
    plt.hist(errors_total, bins=30, alpha=0.7, label='Total Error')
    plt.xlabel('Error (m)')
    plt.ylabel('Frequency')
    plt.title('Total Fusion Error Distribution')
    plt.legend()
    plt.show()

    fig7 = plt.figure()
    plt.hist(errors_x, bins=30, alpha=0.7, label='Longitude Error')
    plt.xlabel('Error (m)')
    plt.ylabel('Frequency')
    plt.title('Longitude Error Distribution')
    plt.legend()
    plt.show()

    fig8 = plt.figure()
    plt.hist(errors_y, bins=30, alpha=0.7, label='Latitude Error')
    plt.xlabel('Error (m)')
    plt.ylabel('Frequency')
    plt.title('Latitude Error Distribution')
    plt.legend()
    plt.show()

    fig9 = plt.figure()
    plt.hist(errors_z, bins=30, alpha=0.7, label='Altitude Error')
    plt.xlabel('Error (m)')
    plt.ylabel('Frequency')
    plt.title('Altitude Error Distribution')
    plt.legend()
    plt.show()


main()
