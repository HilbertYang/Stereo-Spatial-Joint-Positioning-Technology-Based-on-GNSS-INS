
clc;
clear;
close all;
warning off;
addpath(genpath(pwd));

%****************************************************************************
%更多关于matlab和fpga的搜索“fpga和matlab”的CSDN博客:
%matlab/FPGA项目开发合作
%https://blog.csdn.net/ccsss22?type=blog
%****************************************************************************


attiCalculator = AttitudeBase();                            %载入基本的姿态变化关系函数及相关矩阵计算

%基本参数初始化
step = 0.01;                                                %设定步长
start_time = 0;
end_time = 50;                                              %设定测量时间
tspan = [start_time:step:end_time]';
N = length(tspan);
Ar = 10;
r = [Ar*sin(tspan) Ar*cos(tspan) 0.5*tspan];      % gps_pure         %生成实际轨迹数据
v = [Ar*cos(tspan) -Ar*sin(tspan) ones(N,1)];
acc_inertial = [-Ar*sin(tspan) -Ar*cos(tspan) zeros(N,1)];

atti = [0.1*sin(tspan) 0.1*sin(tspan) 0.1*sin(tspan)];
Datti = [0.1*cos(tspan) 0.1*cos(tspan) 0.1*cos(tspan)];
g = [0 0 -9.8]';
gyro_pure = zeros(N,3);
acc_pure = zeros(N,3);
gps_pure= r;

a = wgn(N,1,1)/5;
b = zeros(N,1);
b(1) = a(1)*step;
%生成无噪声的imu数据
for iter = 1:N
    A = attiCalculator.Datti2w(atti(iter,:));
    gyro_pure(iter,:) = Datti(iter,:)*A';
    cnb = attiCalculator.a2cnb(atti(iter,:));
    acc_pure(iter,:) = cnb*(acc_inertial(iter,:)' - g);
end

%给实际值加噪声得到测量值
acc_noise = acc_pure + randn(N,3)/10;           %加速度测量值
gyro_noise = gyro_pure + randn(N,3)/10;         %角速度测量值
gps_noise=[zeros(N,1) gps_pure+randn(N,3)/10];  %GPS测量值
for i=1:10:N
    gps_noise(i,1)=1;
end
state0 = zeros(16,1);
state0(2) = 10;
state0(4) = 10;
state0(7) = 1;

errorstate0=zeros(15,1);%误差初始状态赋值
Cov=[0.01*ones(3,1);zeros(3,1);0.01*ones(3,1);zeros(3,1)];
Qc0=diag(Cov);%初始噪声方差
Rc0=diag([0.01,0.01,0.01]);%GPS测量噪声误差方差

%可以改变量使输入的惯性元件的数据带噪声或者不带
ins = InsSolver(Qc0,Rc0);
[state,errorstate] = ins.imu2state(acc_noise,gyro_noise,gps_noise,state0,errorstate0,tspan,step,0);
%轨迹作图
figure(1)
plot3(r(:,1),r(:,2),r(:,3),'r');
hold on;
plot3(state(:,1),state(:,2),state(:,3),'g');
plot3(gps_noise(:,2),gps_noise(:,3),gps_noise(:,4),'b');
legend('真实轨迹','滤波轨迹','GPS测量轨迹');
xlabel('x/m','fontname','宋体','fontsize',10);
ylabel('y/m','fontname','宋体','fontsize',10);
zlabel('z/m','fontname','宋体','fontsize',10);
grid on;

%三轴位置分别作图
figure(2);
plot(tspan,state(:,1),'b');
hold on;
plot(tspan,gps_noise(:,2),'r');
plot(tspan,r(:,1),'g');
grid on;
legend('滤波后位置','测量位置','实际位置');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('x轴位置/m','fontname','宋体','fontsize',10);

figure(3);
plot(tspan,state(:,2),'b');
hold on;
plot(tspan,gps_noise(:,3),'r');
plot(tspan,r(:,2),'g');
grid on;
legend('滤波后位置','测量位置','实际位置');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('y轴位置/m','fontname','宋体','fontsize',10);

figure(4);
plot(tspan,state(:,3),'b');
hold on;
plot(tspan,gps_noise(:,4),'r');
plot(tspan,r(:,3),'g');
grid on;
legend('滤波后位置','测量位置','实际位置');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('z轴位置/m','fontname','宋体','fontsize',10);


% 三轴位置误差作图
figure(5);
plot(tspan,state(:,1) - r(:,1),'b');
hold on;
plot(tspan,gps_noise(:,2) - r(:,1),'r');
grid on;
legend('滤波后误差','测量误差');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('x轴位置误差/m','fontname','宋体','fontsize',10);

figure(6);
plot(tspan,state(:,2) - r(:,2),'b');
hold on;
plot(tspan,gps_noise(:,3) - r(:,2),'r');
grid on;
legend('滤波后误差','测量误差');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('y轴位置误差/m','fontname','宋体','fontsize',10);

figure(7);
plot(tspan,state(:,3) - r(:,3),'b');
hold on;
plot(tspan,gps_noise(:,4) - r(:,3),'r');
grid on;
legend('滤波后误差','测量误差');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('z轴位置误差/m','fontname','宋体','fontsize',10);