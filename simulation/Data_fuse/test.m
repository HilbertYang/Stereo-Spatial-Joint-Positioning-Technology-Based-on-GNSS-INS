acc_read = xlsread('ACC_2.xlsx');
gyro_read = xlsread('GRY_2.xlsx');
jiaodu = xlsread('ZTJ_2.xlsx');
BDS_curve = xlsread('BDS_2.xlsx');

% 检查数据的大小
disp(size(acc_read));
disp(size(gyro_read));
disp(size(jiaodu));
disp(size(BDS_curve));
