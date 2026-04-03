clc
clear
BDS_curve = xlsread('BDS_2.xlsx');
D = filloutliers(BDS_curve,"nearest","quartiles");% D为剔除异常值后的数据
curve_x=D(:,1);%经度
curve_y=D(:,2);%纬度
curve_z=D(:,3);
m1 = medfilt1(curve_z, 5);% 中值滤波
m2 = medfilt1(m1, 3);
x1=smooth(curve_x);% x1为经度
y1=smooth(curve_y);% y1为纬度
z1 = smooth(m2);%平滑处理
r(:,1) = x1;%经度
r(:,2)= y1;%纬度
r(:,3)= z1;
gps_data= r;
acc_read= xlsread('ACC_2.xlsx');
 acc_data = acc_read/10000;
gyro_read = xlsread('GRY_2.xlsx');
 gyro_data = gyro_read/10000;
jiaodu= xlsread('ZTJ_2.xlsx');

%% 读取数据与处理
% data = importdata('ceshi.txt');

% ATGM332D输出
% gvx  = data.data(:, 1);  % x速度  
% gvy  = data.data(:, 2);  % y速度
% gvz  = data.data(:, 3);  % z速度
gvx = gyro_data(:,1);
gvy = gyro_data(:,2);
gvz = gyro_data(:,3);
% gpsx = data.data(:, 4);  % 经度
% gpsy = data.data(:, 5);  % 纬度
% gpsz = data.data(:, 6);  %高度
gpsx = gps_data(:,1);
gpsy = gps_data(:,2);
gpsz = gps_data(:,3);
%MPU6050输出
% pitch = data.data(:, 7);  % 俯仰角
% rol   = data.data(:, 8);  % 翻滚角
% yaw   = data.data(:, 9);  % 航向角
pitch = jiaodu(:,1);
rol = jiaodu(:,2);
yaw = jiaodu(:,3);
% accx  = data.data(:, 10); % x轴加速度
% accy  = data.data(:, 11); % y轴加速度
% accz  = data.data(:, 12); % z轴加速度
accx  = acc_data(:,1);
accy  = acc_data(:,2);
accz  = acc_data(:,3);
% t  = data.data(:, 13); % 时间戳
% 生成等间隔的时间数据
N = length(acc_data); % 数据点数量
time_interval = 1; % 时间间隔（秒）
t_h = (0:N-1) * time_interval; % 生成时间数组
t = t_h / 3600; % 将时间单位转换为小时

% ATK-MO1218位置初始值
gpsx0 = gpsx(1);
gpsy0 = gpsy(1);
gpsz0 = gpsz(1);
%ATK-MO1218位移量
gps_x = (gpsx - gpsx0);       % 直接只用GPS估算的位移，单位为°E/°N
gps_y = (gpsy - gpsy0) ;      
gps_z = (gpsy - gpsy0);

N = length(accx);           % 循环次数
t_he = zeros(1,N);    % 存储时间t的和
t_he(1) = t(1);       % 初始化时间t1
x = zeros(15,N);    % 状态值，分别为位移、速度、姿态角、角速度、加速度误差信息
%创建测量值空矩阵
z = zeros(6,N);
p = zeros(15,15*N);
H = [eye(6),zeros(6,9)];           % 6x15的观测矩阵
pos_x = zeros(1,N);
pos_y = zeros(1,N);
pos_z = zeros(1,N);
vel_x = zeros(1,N);
vel_y = zeros(1,N);
vel_z = zeros(1,N);

pos_X = zeros(N,1);
pos_Y = zeros(N,1);
pos_Z = zeros(N,1);
vel_X = zeros(N,1);
vel_Y = zeros(N,1);
vel_Z = zeros(N,1);
for k=2:N
    a = 6378136.49;%地球半径，单位：m
    b = 6356755.00;
    R_b = [cos(pi/180*yaw(k-1))*cos(pi/180*pitch(k-1)), cos(pi/180*yaw(k-1))*sin(pi/180*pitch(k-1))*sin(pi/180*rol(k-1))-sin(pi/180*yaw(k-1))*cos(pi/180*rol(k-1)), sin(pi/180*yaw(k-1))*sin(pi/180*rol(k-1))+cos(pi/180*yaw(k-1))*sin(pi/180*pitch(k-1))*cos(pi/180*rol(k-1));
           sin(yaw(k-1)*pi/180)*cos(pitch(k-1)*pi/180), cos(yaw(k-1)*pi/180)*cos(rol(k-1)*pi/180)+sin(yaw(k-1)*pi/180)*sin(pitch(k-1)*pi/180)*sin(rol(k-1)*pi/180), sin(yaw(k-1)*pi/180)*sin(pitch(k-1)*pi/180)*cos(rol(k-1)*pi/180)-cos(yaw(k-1)*pi/180)*sin(rol(k-1)*pi/180);
                   -sin(pitch(k-1)*pi/180)          ,    cos(yaw(k-1)*pi/180)*sin(rol(k-1)*pi/180)    ,     cos(yaw(k-1)*pi/180)*cos(rol(k-1)*pi/180);]; % 转移矩阵.
    D_1 = [    0   ,1/(a+25),0;
         1/(b+25),    0   ,0;
             0   ,    0   ,1];
    D_2 = [    0    ,1/(a+25),0;
           -1/(b+25),    0   ,0;
           -0.0000001/(b+25),0,0];
    D_3 = [  0  , accz(k-1,:) ,-accy(k-1,:);
           -accz(k-1,:),  0   ,accx(k-1,:);
            accy(k-1,:),-accx(k-1,:) ,  0];
    D_4 = eye(3)*(-1/t(k));
    F_t = [zeros(3,3),eye(3),zeros(3,9);
           zeros(3,6),D_2,zeros(3,3),R_b;
           zeros(3,6),-D_3,-R_b,zeros(3,3);
           zeros(3,9),D_4,zeros(3,3);
           zeros(3,12),D_4];
    F = eye(15) + F_t .* t(k);% 状态转移矩阵
    G = diag([0,0,0,0,0,0,0,0,0,0.1,0.1,0.1,0.1,0.1,0.1]);
    G = G .* t(k);
    Q = diag([10,10,10,0.1,0.1,0.1,1,1,1,1/0.36 ,1/0.36 ,1/0.36 ,10,10,10]);% 过程噪声协方差，估计一个
    R = diag([6.25,6.25,6.25,0.01,0.01,0.01]);
    p(:,1:15) = eye(15);                             % 初始值为 1（可为非零任意数） 
    x(:,1) = zeros(15,1);
    t_he(k) = t_he(k-1) + t(k);
    velx = cumsum(accx(1:k) .* t(1:k));   % 积分计算x速度
    vely = cumsum(accy(1:k) .* t(1:k));   % 积分计算y速度
    velz = cumsum(accz(1:k) .* t(1:k));   % 积分计算z速度
    posx = cumsum(velx(1:k) .* t(1:k));   % 积分计算x位移
    posy = cumsum(vely(1:k) .* t(1:k));   % 积分计算y位移
    posz = cumsum(velz(1:k) .* t(1:k));   % 积分计算z位移
    z(:,k)= [posx(k) - gps_x(k);
              posy(k) - gps_y(k);
              posz(k) - gps_z(k);
              velx(k) - gvx(k);
              vely(k) - gvy(k);
              velz(k) - gvz(k)];   % 测量矩阵
 
    % 离散卡尔曼公式
    x(:,k) = F * x(:,k-1);                   % 卡尔曼公式1  得到预估值
    p(:,15*k-14:15*k) = F * p(:,15*(k-2)+1:15*(k-1)) * F' + G * Q * G';    % 卡尔曼公式2
    K = p(:,15*k-14:15*k) * H'/( H * p(:,15*k-14:15*k) * H' +  R );        % 卡尔曼公式3  计算卡尔曼增益                                     
    x(:,k) =  x(:,k) + K * (z(:,k) - H * x(:,k));                          % 卡尔曼公式4  校正预估值
    p(:,15*k-14:15*k) = (eye(15) - K * H) * p(:,15*k-14:15*k);             % 卡尔曼公式5
    pos_X(k) = (posx(k) -  x(1,k)');
    pos_Y(k) = (posy(k) -  x(2,k)');
    pos_Z(k) = (posz(k) -  x(3,k)');
    vel_X(k) = (velx(k) - x(4,k)');
    vel_Y(k) = (vely(k) -  x(5,k)');
    vel_Z(k) = (velz(k) -  x(6,k)');

    t_he = t_he(1,:);
end


% 卡尔曼滤波计算速度、位移
[velx_km, posx_km, ~, km_ce1x,km_ce2x] = kalman(t, accx, gps_x);
[vely_km, posy_km, ~, km_ce1y,km_ce2y] = kalman(t, accy, gps_y);
[velz_km, posz_km, t_he, km_ce1z,km_ce2z] = kalman(t, accz, gps_z);



gps_x=(gpsx-gpsx0);
gps_y=(gpsy-gpsy0);
gps_z=(gpsz-gpsz0);


gps_x_noise=(curve_x-gpsx0);
gps_y_noise=(curve_y-gpsy0);
gps_z_noise=(curve_z-gpsz0);

% figure(10);
% plot3(gps_x,gps_y,gps_z,'b');



%% KF结果分析
%% KF（位置）
figure(1);subplot(311);
 plot(t_he,posx,'b');
hold on
 plot(t_he,gps_x_noise, 'g');
plot(t_he,posx_km,'r'); hold off
a1 = legend('积分', 'KF','Location','BestOutside');
% a1.ItemTokenSize =[15,10];
title('距离');
xlabel('时间t/s');
ylabel('x方向位移 (m)');

subplot(312);
 plot(t_he,posy,'b');
hold on
 plot(t_he,gps_y_noise,'g');
plot(t_he,posy_km,'r'); hold off
a2=legend('积分', 'KF','Location','BestOutside');
a2.ItemTokenSize =[15,10];
xlabel('时间t/s');
ylabel('y方向位移 (m)');

subplot(313);
 plot(t_he,posz,'b');
hold on
 plot(t_he,abs(gps_z_noise),'g');
plot(t_he,posz_km,'r'); hold off
a3=legend('积分','KF','Location','BestOutside');
a3.ItemTokenSize =[15,10];
xlabel('时间t/s)');ylabel('z方向位移 (m)');

%% KF（速度）
figure(2);subplot(311);
plot(t_he, velx,'b');hold on
% plot(t_he, km_ce2x,'g');hold on
plot(t_he, velx_km,'r');
hold off
a4=legend('积分','KF','Location','BestOutside');
a4.ItemTokenSize =[15,10];
title('速度');
xlabel('时间t/s');
ylabel('x轴速度 (m/s)');

subplot(312);
plot(t_he, vely,'b');hold on 
% plot(t_he, km_ce2y,'g');hold on
plot(t_he, vely_km,'r');hold off
a5=legend('积分','KF','Location','BestOutside');
a5.ItemTokenSize =[15,10];
xlabel('时间t/s');
ylabel('y轴速度 (m/s)');

subplot(313);
plot(t_he, velz,'b');hold on
% plot(t_he, km_ce2z,'g');hold on
plot(t_he, velz_km,'r');hold off
a6=legend('积分','KF','Location','BestOutside');
a6.ItemTokenSize =[15,10];
xlabel('时间t (s)');ylabel('z轴速度 (m/s)');



%% EKF结果分析
%% EKF（位置）
figure(3);subplot(311);
plot(t_he,posx,'b');hold on
%  plot(t_he,gps_x, 'g');
plot(t_he,pos_X,'r'); hold off
a7=legend('积分', 'KF','Location','BestOutside');
a7.ItemTokenSize =[15,10];
title('距离');xlabel('时间t (s)');ylabel('x方向距离 (m)');

subplot(312);
plot(t_he,posy,'b');hold on
% plot(t_he,gps_y,'g');
plot(t_he,pos_Y,'r'); hold off
a8=legend('积分','KF','Location','BestOutside');
a8.ItemTokenSize =[15,10];xlabel('时间t (s)');
ylabel('y方向距离 (m)');

subplot(313);
plot(t_he,posz,'b');hold on
% plot(t_he,gps_z,'g');
plot(t_he,pos_Z,'r'); hold off
a9=legend('积分','KF','Location','BestOutside');
a9.ItemTokenSize =[15,10];
xlabel('时间t (s)');ylabel('z方向距离 (m)');


%% （误差）
% figure(5)
% plot3(pos_X, pos_Y, pos_Z,'b','MarkerSize',1);hold on
% plot3(gps_x, gps_y, gps_z,'r','MarkerSize',0.5);hold on
% plot3(posx_km,posy_km, posz_km,'g','MarkerSize',1);hold off
% legend('ESKF','测量值', 'KF');

KF_v = zeros(N,1);
KF_x = zeros(N,1);
EKF_v = zeros(N,1);
EKF_x = zeros(N,1);
for k=2:N
KF_v(k) = sqrt((velx_km(k)-km_ce2x(k))^2 + (vely_km(k)-km_ce2y(k))^2)/10 ;
KF_x(k) = sqrt((posx_km(k)-gps_x(k))^2 + (posy_km(k)-gps_y(k))^2)/2;
EKF_v(k) = sqrt((vel_X(k)-km_ce2x(k))^2 + (vel_Y(k)-km_ce2y(k))^2)/8 ;
EKF_x(k) = sqrt((pos_X(k)-gps_x(k))^2 + (pos_Y(k)-gps_y(k))^2)/3 ;
end

figure(6);subplot(211);
plot(t_he, KF_x ,'b');
hold on;
% ylim([0,400]);
% plot(t_he, EKF_x , 'r');hold off
a10=legend('KF','Location','BestOutside');
% a10.ItemTokenSize =[15,10];
title('误差');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('位移/m','fontname','宋体','fontsize',10);

subplot(212);
plot(t_he,KF_v,'b');hold on
% plot(t_he,EKF_v ,'r'); hold off
a11=legend('KF','Location','BestOutside');
a11.ItemTokenSize =[15,10];
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('速度/m','fontname','宋体','fontsize',10);



%% EKF（速度）
figure(4);subplot(311);
plot(t_he, velx,'b');hold on
% plot(t_he, gvx,'g');hold on
plot(t_he, vel_X,'r');
hold off
a12=legend('积分','KF','Location','BestOutside');
a12.ItemTokenSize =[15,10];
title('速度');xlabel('时间t/s');ylabel('x轴速度 (m/s)');

subplot(312);
plot(t_he, vely,'b');hold on 
%  plot(t_he, gvy,'g');hold on
plot(t_he, vel_Y,'r');hold off
a13=legend('积分','KF','Location','BestOutside');
a13.ItemTokenSize =[15,10];
xlabel('时间t/s');ylabel('y轴速度 (m/s)');

subplot(313);
plot(t_he, velz,'b');hold on
% plot(t_he, gvz,'g');hold on
plot(t_he, vel_Z,'r');hold off
a14=legend('积分','KF','Location','BestOutside');
a14.ItemTokenSize =[15,10];
xlabel('时间t (s)');ylabel('z轴速度 (m/s)');


%% 卡尔曼滤波
function [vel, pos,t_he,ce1,ce2] = kalman(t, acc, gps)

H = [1,0;0,1];                              % 转换矩阵
Q = [0.00001 0; 0 0.00001];                   % 过程噪声协方差，估计一个
R = [6.25,0;0,0.01];
P = eye(2);                             % 初始值为 1（可为非零任意数） 
N = length(acc);
x = zeros(2, N);                        % 存储滤波后的数据，分别为位移、速度信息
t_he = zeros(1,N);    % 存储t的和
t_he(1) = t(1);
z_=zeros(2,N);    %创建实际值空矩阵
for k=2:N
    dt = t(k);
    A = [1 dt; 0 1];                            % 状态转移矩阵
    B = [1/2*dt^2; dt];                         % 输入控制矩阵
    t_he(k) = t_he(k-1) + t(k);
    x(:,k) = A * x(:,k-1) + B*acc(k,1) + sqrtm(Q)*randn(2,1);         % 卡尔曼公式1
    z_(:,k)= [gps(k)-gps(k-1); 0];           % 测量值
    P = A * P * A' + Q;                         % 卡尔曼公式2
    K = P*H'/(H*P*H' + R);                 % 卡尔曼公式3                                       
    x(:,k) = x(:,k) + K * (z_(k)-H*x(:,k));    % 卡尔曼公式4
    P = (eye(2)-K*H) * P;                       % 卡尔曼公式5
end
pos = x(1,:)';
vel = x(2,:)';
ce1 = z_(1,:)';
ce2 = z_(2,:)';
t_he = t_he(1,:);
end      % 过程噪声协方差，估计一个


