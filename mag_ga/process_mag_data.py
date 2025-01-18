import pandas as pd
import numpy as np

def process_mag_data(input_file, output_file):
    # 读取CSV文件
    df = pd.read_csv(input_file)
    
    # 初始化变量
    cumulative_error = 0
    rows_to_drop = []
    i = 0
    
    while i < len(df) - 1:
        # 计算相邻时间点的差值
        time_diff = df.iloc[i+1]['Time'] - df.iloc[i]['Time']
        
        # 如果时间差小于0.01
        if time_diff < 0.01:
            # 计算与0.01的差值并累计
            error = 0.01 - time_diff
            cumulative_error += error
            
            # 如果累计误差达到0.003
            if cumulative_error >= 0.003:
                # 对所有数值列取平均值
                for col in ['X', 'Y', 'Z', 'Magnitude', 'Filtered Magnitude']:
                    df.iloc[i][col] = (df.iloc[i][col] + df.iloc[i+1][col]) / 2
                
                # 标记需要删除的行
                rows_to_drop.append(i+1)
                
                # 重置累计误差
                cumulative_error = 0
                
                # 跳过下一行，因为它已经被处理
                i += 2
                continue
        else:
            # 如果时间差正常，重置累计误差
            cumulative_error = 0
            
        i += 1
    
    # 删除标记的行
    df = df.drop(rows_to_drop)
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    # 保存处理后的数据
    df.to_csv(output_file, index=False)
    
    return len(rows_to_drop)  # 返回删除的行数

if __name__ == "__main__":
    import sys
    import os
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print("请提供输入文件路径")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 生成输出文件名
    filename = os.path.basename(input_file)
    base_name = os.path.splitext(filename)[0]
    output_file = os.path.join(os.path.dirname(input_file), f"{base_name}_processed.csv")
    
    # 处理数据
    deleted_rows = process_mag_data(input_file, output_file)
    print(f"处理完成！")
    print(f"删除了 {deleted_rows} 行数据")
    print(f"处理后的文件保存为: {output_file}")
