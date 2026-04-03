%%
%读取数据文件
BDS_straight = xlsread('BDS_2.xlsx');
% BDS_curve = xlsread('BDS_2.xlsx');

%%
%进行异常值的剔除与补全
A = rmoutliers(BDS_straight,"quartiles");
B = rmoutliers(BDS_curve);
C = filloutliers(BDS_straight,"nearest","quartiles");
D = filloutliers(BDS_curve,"nearest");
% B = rmoutliers(A) 在 A 的数据中检测并删除离群值。
% 如果 A 是矩阵，则 rmoutliers 会分别检测 A 的每列中的离群值，并删除整行。
% 如果 A 是表或时间表，则 rmoutliers 会分别检测 A 的每个变量中的离群值并删除整行。
% 默认情况下，离群值是指与中位数相差超过三倍经过换算的中位数绝对偏差 (MAD) 的值。
% 实验中使用rmoutliers(A,"mean") 将 A 中与均值相差超过三倍标准差的元素定义为离群值。
% B = filloutliers(A,fillmethod) 查找 A 中的离群值并根据 fillmethod 替换它们。
% 例如，filloutliers(A,"previous") 将离群值替换为上一个非离群值元素。
%找到异常值的位置
%idx = m >1.7; %逻辑运算符<=会返回一个逻辑数组idx，可以作为索引来选择需要绘制的数据。
%%
%滤波和平滑处理
% 使用移动平均滤波器
% smoothed_data = smooth(data, window_size);
% plot(smoothed_data);

% 中值滤波器： 与平均滤波器类似，但是计算窗口内数据的中值。中值滤波器对于处理离群值（如尖点）更为鲁棒。
% a = C(:,1);
% b = medfilt1(a, 5);
% plot(smoothed_data);

u=A(:,1);
v=A(:,2);
w=A(:,3);

u1_1=C(:,1);
v1_1=C(:,2);
w1=C(:,3);
a = medfilt1(w1, 5);
u1 = smooth(u1_1);
v1= smooth(v1_1);


x=B(:,1);
y=B(:,2);
z=B(:,3);

x1_1=D(:,1);
y1_1=D(:,2);
z1=D(:,3);
c = medfilt1(z1, 5);% 中值滤波
cc = medfilt1(c, 3);

x1=smooth(x1_1);
y1=smooth(y1_1);
b = smooth(cc);%平滑处理

%%
%绘图
figure(1);
hold on;
plot3(u,v,w,'r');
% plot3(u(1), v(1),w(1),'or', 'MarkerSize', 8, 'LineWidth', 2);
axis tight;
ylim([31.56,31.62]);
zlim([0,20]);
legend('直线轨迹');
xlabel('JD/°E','fontname','宋体','fontsize',10);
ylabel('WD/°N','fontname','宋体','fontsize',10);
zlabel('HIGH/m','fontname','宋体','fontsize',10);
grid

figure(2);
hold on;
plot3(u1,v1,a,'r','LineWidth', 2);
plot3(u1(1), v1(1),a(1), 'or', 'MarkerSize', 8, 'LineWidth', 2);
axis tight;
ylim([31.56,31.62]);
zlim([0,20]);
legend('直线轨迹');
xlabel('JD/°E','fontname','宋体','fontsize',20);
ylabel('WD/°N','fontname','宋体','fontsize',20);
zlabel('HIGH/m','fontname','宋体','fontsize',20);
grid

figure(3);
hold on;
plot3(x,y,z,'r');
plot3(x(1), y(1),z(1), 'or', 'MarkerSize', 8, 'LineWidth', 5);
axis tight;
ylim([31.56,31.62]);
zlim([0,20]);
legend('曲线轨迹');
xlabel('JD/°E','fontname','宋体','fontsize',20);
ylabel('WD/°N','fontname','宋体','fontsize',20);
zlabel('HIGH/m','fontname','宋体','fontsize',20);
grid

figure(4);
hold on;
plot3(x1,y1,b,'r','LineWidth', 2);
plot3(x1(1), y1(1),b(1), 'or', 'MarkerSize', 15, 'LineWidth', 2);
% plot3(x1, y1,b,'-o','MarkerIndices',1);
axis tight;
ylim([31.56,31.62]);
zlim([0,20]);
legend('曲线轨迹');
xlabel('JD/°E','fontname','宋体','fontsize',20);
ylabel('WD/°N','fontname','宋体','fontsize',20);
zlabel('HIGH/m','fontname','宋体','fontsize',20);
grid

figure(5);

subplot(311)
plot(BDS_curve(:,3),'r');
legend('原始数据');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('高度/m','fontname','宋体','fontsize',10);
grid

subplot(312)
plot(z1,'r');
legend('剔除异常值后的数据');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('高度/m','fontname','宋体','fontsize',10);
grid

subplot(313)
plot(b,'r');
legend('滤波+平滑后的数据');
xlabel('时间/s','fontname','宋体','fontsize',10);
ylabel('高度/m','fontname','宋体','fontsize',10);
grid

