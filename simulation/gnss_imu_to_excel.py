from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd


filename = 'target_corrected.txt'



JD, WD, HIGH, speed = [], [], [], []  # 经纬度和高度速度
ACC_X, ACC_Y, ACC_Z, GRY_X, GRY_Y, GRY_Z = [], [], [], [], [], []  # 加速度值和角速度值
pit, rol, yaw = [], [], []  # 姿态角
# 相比open(),with open()不用手动调用close()方法
with open(filename, 'r') as f:
    # 将txt中的数据逐行存到列表lines里 lines的每一个元素对应于txt中的一行。然后将每个元素中的不同信息提取出来
    lines = f.readlines()
    # i变量，由于这个txt存储时有空行，所以增只读偶数行，主要看txt文件的格式，一般不需要
    # 使用i读取只有北斗数据的行，提取需要的数据
    i = 0
    for line in lines:
        if i % 2 == 1:
            temp = line.split("E")  # 分割精度和其他数据
            a = temp[1].split("N")  # 分割纬度和其他数据
            b = a[1].split('m')  # 分割高度和其他数据
            JD.append(float(temp[0].strip().replace("'", "")))  # 去除单引号并转换为浮点数
            WD.append(float(a[0].strip().replace("'", "")))
            HIGH.append(float(b[0].strip().replace("'", "")))
            i = i + 1
        else:
            i = i + 1
            c = line.split(",")
            o = c[0].split("pit:")
            p = c[1].split("rol:")
            q = c[2].split("yaw:")

            d = c[3].split("acc_x:")
            e = c[4].split("acc_y:")
            g = c[5].split("acc_z:")
            h = c[6].split("gyr_x:")
            m = c[7].split("gyr_y:")
            n = c[8].split("gyr_z:")
            pit.append(str(o[1]))
            rol.append(str(p[1]))
            yaw.append(str(q[1]))
            ACC_X.append(str(d[1]))
            ACC_Y.append(str(e[1]))
            ACC_Z.append(str(g[1]))
            GRY_X.append(str(h[1]))
            GRY_Y.append(str(m[1]))
            GRY_Z.append(str(n[1]))

print(JD)  # 打印出来数组，确保数据正确
print(WD)
print(HIGH)
print(ACC_X)  # 打印出来数组，确保数据正确
print(ACC_Y)
print(ACC_Z)
print(GRY_X)  # 打印出来数组，确保数据正确
print(GRY_Y)
print(GRY_Z)

# data = [JD, WD, HIGH]  # 将读取的数组文件保存到data中，并得到数组形式的文件
# with open("./BDS_5.6.txt", "w") as file:
#     for row in data:
#         for item in row:
#             file.write(str(item) + ',')
#         file.write('\n')

data = pd.DataFrame({'JD': JD, 'WD': WD, 'HIGH': HIGH})
# data.to_excel('BDS_1.xlsx', index=False) # 直线行走数据保存位置，后缀编号为1
data.to_excel('BDS_2.xlsx', index=False)  # 曲线行走数据保存位置，后缀编号为2

# data = [ACC_X, ACC_Y, ACC_Z]  # 将读取的数组文件保存到data中，并得到数组形式的文件
# with open("./ACC_data.txt", "w") as file:
#     for row in data:
#         for item in row:
#             file.write(str(item) + ' ')
#         file.write('\n')
data = pd.DataFrame({'ACC_X': ACC_X, 'ACC_Y': ACC_Y, 'ACC_Z': ACC_Z})
# data.to_excel('ACC_1.xlsx', index=False)
data.to_excel('ACC_2.xlsx', index=False)

# data = [GRY_X, GRY_Y, GRY_Z]  # 将读取的数组文件保存到data中，并得到数组形式的文件
# with open("./GRY_data.txt", "w") as file:
#     for row in data:
#         for item in row:
#             file.write(str(item) + ' ')
#         file.write('\n')

data = pd.DataFrame({'GRY_X': GRY_X, 'GRY_Y': GRY_Y, 'GRY_Z': GRY_Z})
# data.to_excel('GRY_1.xlsx', index=False)
data.to_excel('GRY_2.xlsx', index=False)

data = pd.DataFrame({'PIT': pit, 'ROL': rol, 'YAW': yaw})
# data.to_excel('GRY_1.xlsx', index=False)
data.to_excel('ZTJ_2.xlsx', index=False)
# # new a figure and set it into 3d
# fig = plt.figure()
# # ax = fig.gca(projection='3d')
# ax = fig.add_axes(Axes3D(fig))  # 上一行代码报错，查找资料后使用本行代码成功显示图像
#
# # set figure information
# ax.set_title("3D_Curve")
# ax.set_xlabel("x")
# ax.set_ylabel("y")
# ax.set_zlabel("z")
#
# # draw the figure, the color is r = read
# figure = ax.plot(JD, WD, HIGH, c='r')
# plt.show()

def line_3d():
    # 线图
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    # c颜色，marker：样式*雪花
    ax.plot(xs=JD, ys=WD, zs=HIGH, c="y", marker="*")
    plt.show()


def scatter_3d():
    # 散点图
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.set_title("Trajectory scatter plot")
    ax.set_xlabel("JD/°E")
    ax.set_ylabel("WD/°N")
    ax.set_zlabel("HIGH/m")

    # s：marker标记的大小
    # c: 颜色  可为单个，可为序列
    # depthshade: 是否为散点标记着色以呈现深度外观。对 scatter() 的每次调用都将独立执行其深度着色。
    # marker：样式
    ax.scatter(xs=JD, ys=WD, zs=HIGH, zdir='z', s=30, c="g", depthshade=True, marker="^")
    plt.show()


line_3d()
# scatter_3d()
