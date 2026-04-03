clc;
clear;

% 读取processed_data.xlsx数据
[num, txt, raw] = xlsread('processed_data.xlsx');
lat = num(:, 1);
lon = num(:, 2);
alt = num(:, 3);
pit = num(:, 4);
rol = num(:, 5);
yaw = num(:, 6);
acc_x = num(:, 7);
acc_y = num(:, 8);
acc_z = num(:, 9);
gyr_x = num(:, 10);
gyr_y = num(:, 11);
gyr_z = num(:, 12);

% 数据预处理
D = filloutliers([lat, lon, alt], "nearest", "quartiles"); % 剔除异常值
curve_x = D(:, 1); % 经度
curve_y = D(:, 2); % 纬度
curve_z = D(:, 3); % 高度

% 中值滤波和平滑处理
m1 = medfilt1(curve_z, 5);
m2 = medfilt1(m1, 3);
x1 = smooth(curve_x);
y1 = smooth(curve_y);
z1 = smooth(m2);

% 整理GPS数据
gps_data = [x1, y1, z1];

% 初始化卡尔曼滤波器参数
dt = 0.1; % 采样时间
A = [1 0 dt 0; 0 1 0 dt; 0 0 1 0; 0 0 0 1]; % 状态转移矩阵
B = [0.5*dt^2 0; 0 0.5*dt^2; dt 0; 0 dt]; % 控制输入矩阵
C = [1 0 0 0; 0 1 0 0]; % 观测矩阵

% 初始估计误差协方差矩阵
P = eye(4); % 估计误差协方差
x = [lat(1); lon(1); 0; 0]; % 初始状态，包括位置和速度

% 过程噪声协方差矩阵
Q = 0.01 * eye(4); % 调整这个值进行优化

% 观测噪声协方差矩阵
R = 0.1 * eye(2); % 调整这个值进行优化

% 存储滤波结果
numDataPoints = length(lat);
x_filtered = zeros(numDataPoints, 4);
x_filtered(1, :) = x';

for i = 2:numDataPoints
    % 状态预测
    u = [acc_x(i); acc_y(i)]; % 控制输入
    x = A * x + B * u;
    P = A * P * A' + Q;
    
    % 卡尔曼增益
    K = P * C' / (C * P * C' + R);
    
    % 更新状态
    z = [lat(i); lon(i)]; % 观测值
    x = x + K * (z - C * x);
    P = (eye(4) - K * C) * P;
    
    % 存储结果
    x_filtered(i, :) = x';
end

% 绘制原始数据路径
figure;
plot(lon, lat, 'r-', 'DisplayName', '原始路径');
hold on;

% 绘制滤波后数据路径
plot(x_filtered(:, 2), x_filtered(:, 1), 'b-', 'DisplayName', '滤波路径');

% 设置图例和标题
legend;
xlabel('经度');
ylabel('纬度');
title('惯导和北斗定位数据路径');

% 保存图表
saveas(gcf, 'filtered_path.png');

