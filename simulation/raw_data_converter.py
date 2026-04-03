def convert_format(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("pit:"):
                data_line = lines[i].strip()
                position_line = lines[i + 2].strip().replace("bd.position: ", "")
                altitude_line = lines[i + 3].strip().replace("bd.altitude: ", "")
                speed_line = lines[i + 4].strip().replace("Speed: ", "")

                # 验证 altitude_line 是否有两个负号
                if altitude_line.count('-') <= 1:
                    # 组合数据行、位置信息行和速度行，写入到输出文件
                    outfile.write(f"{data_line}\n{position_line} {altitude_line} {speed_line}\n")

                # 跳到下一组数据的起始行
                i += 5
            else:
                i += 1


# 输入文件和输出文件路径
input_file = '2014715.txt'
output_file = 'sample3.txt'

# 调用函数进行转换
convert_format(input_file, output_file)

print("转换完成")
