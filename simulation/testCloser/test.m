% GNSS 和 INS 紧组合仿真
clc; clear; close all;

%% 参数设置
dt = 0.01; % 采样周期 (s)
sim_time = 100; % 仿真总时间 (s)
steps = sim_time / dt; % 仿真步数
g = 9.81; % 重力加速度 (m/s^2)

% IMU误差
acc_bias = [0.01; -0.02; 0.015]; % 加速度计零偏 (m/s^2)
gyro_bias = [0.001; 0.002; -0.001]; % 陀螺仪零偏 (rad/s)

% GNSS测量噪声
gnss_noise_pos = 2; % GNSS 位置噪声 (m)

gnss_noise_vel = 0.2; % GNSS 速度噪声 (m/s)

% 初始位置、速度和姿态
true_pos = [0; 0; 0]; % 初始位置 (m)
true_vel = [10; 0; 0]; % 初始速度 (m/s)
true_att = eye(3); % 初始姿态 (单位矩阵)

% 初始状态估计
est_pos = [0; 0; 0]; % 初始估计位置 (m)
est_vel = [10; 0; 0]; % 初始估计速度 (m/s)
est_att = eye(3); % 初始估计姿态 (单位矩阵)

% 状态协方差
P = diag([10 10 10 1 1 1 0.1 0.1 0.1]); % 初始状态协方差矩阵

% IMU噪声
imu_acc_noise = 0.05; % 加速度计噪声 (m/s^2)
imu_gyro_noise = 0.001; % 陀螺仪噪声 (rad/s)

%% 数据存储
pos_hist = zeros(3, steps); % 存储真实位置
vel_hist = zeros(3, steps); % 存储真实速度
pos_est_hist = zeros(3, steps); % 存储估计位置
vel_est_hist = zeros(3, steps); % 存储估计速度
error_hist = zeros(3, steps); % 存储位置误差

%% 仿真循环
for k = 1:steps
    % 时间更新
    t = k * dt;

    % --------------------
    % 1. 真实运动学模型 (模拟真实运动)
    % --------------------
    acc_true = [0; 0; 0]; % 假设没有额外加速度
    gyro_true = [0; 0; 0]; % 假设无旋转运动
    
    % 更新真实位置和速度
    true_vel = true_vel + acc_true * dt;
    true_pos = true_pos + true_vel * dt;

    % --------------------
    % 2. 模拟IMU测量值
    % --------------------
    acc_meas = acc_true + acc_bias + imu_acc_noise * randn(3, 1);
    gyro_meas = gyro_true + gyro_bias + imu_gyro_noise * randn(3, 1);

    % --------------------
    % 3. INS预测 (利用IMU数据更新状态)
    % --------------------
    est_vel = est_vel + (est_att * acc_meas + [0; 0; g]) * dt;
    est_pos = est_pos + est_vel * dt;
    est_att = est_att * (eye(3) + skew(gyro_meas) * dt);

    % --------------------
    % 4. 模拟GNSS观测值
    % --------------------
    if mod(k, 10) == 0 % GNSS每10个时刻提供一次观测
        gnss_pos = true_pos + gnss_noise_pos * randn(3, 1);
        gnss_vel = true_vel + gnss_noise_vel * randn(3, 1);

        % --------------------
        % 5. EKF更新
        % --------------------
        % 状态向量：[位置; 速度; 零偏]
        x = [est_pos; est_vel; acc_bias];

        % 观测向量
        z = [gnss_pos; gnss_vel];

        % 状态转移矩阵 (线性化)
        F = eye(9);
        F(1:3, 4:6) = eye(3) * dt;

        % 观测矩阵
        H = [eye(3), zeros(3, 6); zeros(3, 3), eye(3), zeros(3, 3)];

        % 预测协方差
        Q = diag([0.1 0.1 0.1 0.1 0.1 0.1 0.01 0.01 0.01]); % 过程噪声
        P = F * P * F' + Q;

        % 观测噪声
        R = diag([gnss_noise_pos^2, gnss_noise_pos^2, gnss_noise_pos^2, ...
                  gnss_noise_vel^2, gnss_noise_vel^2, gnss_noise_vel^2]);

        % 卡尔曼增益
        K = P * H' / (H * P * H' + R);

        % 更新状态
        x = x + K * (z - H * x);

        % 更新协方差
        P = (eye(size(K, 1)) - K * H) * P;

        % 提取更新后的状态
        est_pos = x(1:3);
        est_vel = x(4:6);
        acc_bias = x(7:9);
    end

    % --------------------
    % 6. 数据存储
    % --------------------
    pos_hist(:, k) = true_pos;
    vel_hist(:, k) = true_vel;
    pos_est_hist(:, k) = est_pos;
    vel_est_hist(:, k) = est_vel;
    error_hist(:, k) = true_pos - est_pos;
end

%% 绘图结果
figure;
subplot(3, 1, 1);
plot(1:steps, pos_hist(1, :), 'b', 1:steps, pos_est_hist(1, :), 'r--');
xlabel('Time step'); ylabel('Position X (m)'); legend('True', 'Estimated');

subplot(3, 1, 2);
plot(1:steps, pos_hist(2, :), 'b', 1:steps, pos_est_hist(2, :), 'r--');
xlabel('Time step'); ylabel('Position Y (m)'); legend('True', 'Estimated');

subplot(3, 1, 3);
plot(1:steps, error_hist(1, :), 'g');
xlabel('Time step'); ylabel('Position Error X (m)'); legend('Error');

%% 辅助函数：skew 矩阵
function S = skew(v)
    % 输入：3x1向量 v
    % 输出：对应的3x3反对称矩阵 S
    S = [  0    -v(3)   v(2);
          v(3)   0     -v(1);
         -v(2)  v(1)    0  ];
end
