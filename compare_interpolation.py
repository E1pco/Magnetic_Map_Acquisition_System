import pandas as pd
import numpy as np
from pathlib import Path

def evaluate_interpolation(original_df, interpolated_df):
    print("=== 插值效果统计 ===\n")
    
    # 1. 加速度数据评估
    print("1. 加速度数据:")
    acc_cols = [col for col in interpolated_df.columns if 'acceleration' in col]
    for col in acc_cols:
        if col in interpolated_df.columns:
            orig_std = interpolated_df[col].std()
            interp_std = interpolated_df[col].std()
            std_change = (interp_std - orig_std) / orig_std * 100 if orig_std != 0 else 0
            
            print(f"{col}:")
            print(f"  - 原始数据标准差: {orig_std:.8f}")
            print(f"  - 插值后标准差: {interp_std:.8f}")
            print(f"  - 标准差变化率: {std_change:.2f}%")
    
    # 2. 磁力计数据评估
    print("\n2. 磁力计数据:")
    # 原始数据列名是大写的 X, Y, Z
    # 插值后数据列名是小写的 x, y, z
    mag_pairs = [('X', 'x'), ('Y', 'y'), ('Z', 'z')]
    
    for orig_col, interp_col in mag_pairs:
        if orig_col in original_df.columns and interp_col in interpolated_df.columns:
            # 获取有效数据
            orig_data = original_df[orig_col].dropna()
            interp_data = interpolated_df[interp_col].dropna()
            
            if len(orig_data) > 0 and len(interp_data) > 0:
                # 计算中位数绝对偏差 (MAD)
                orig_mad = np.median(np.abs(orig_data - np.median(orig_data)))
                interp_mad = np.median(np.abs(interp_data - np.median(interp_data)))
                mad_change = (interp_mad - orig_mad) / orig_mad * 100 if orig_mad != 0 else 0
                
                # 计算四分位数范围 (IQR)
                orig_q75, orig_q25 = np.percentile(orig_data, [75, 25])
                interp_q75, interp_q25 = np.percentile(interp_data, [75, 25])
                orig_iqr = orig_q75 - orig_q25
                interp_iqr = interp_q75 - interp_q25
                iqr_change = (interp_iqr - orig_iqr) / orig_iqr * 100 if orig_iqr != 0 else 0
                
                # 计算最大变化率（使用固定的时间间隔0.01s）
                orig_max_rate = np.max(np.abs(np.diff(orig_data))) / 0.01
                interp_max_rate = np.max(np.abs(np.diff(interp_data))) / 0.01
                rate_change = (interp_max_rate - orig_max_rate) / orig_max_rate * 100 if orig_max_rate != 0 else 0
                
                print(f"\n{orig_col}轴:")
                print("  中位数绝对偏差(MAD):")
                print(f"    - 原始数据: {orig_mad:.8f}")
                print(f"    - 插值后: {interp_mad:.8f}")
                print(f"    - 变化率: {mad_change:.2f}%")
                
                print("  四分位数范围(IQR):")
                print(f"    - 原始数据: {orig_iqr:.8f}")
                print(f"    - 插值后: {interp_iqr:.8f}")
                print(f"    - 变化率: {iqr_change:.2f}%")
                
                print("  最大连续变化率:")
                print(f"    - 原始数据: {orig_max_rate:.8f}/s")
                print(f"    - 插值后: {interp_max_rate:.8f}/s")
                print(f"    - 变化率: {rate_change:.2f}%")
                
                print("  数据分布:")
                print(f"    - 原始数据: 均值={orig_data.mean():.8f}, 标准差={orig_data.std():.8f}")
                print(f"    - 插值后: 均值={interp_data.mean():.8f}, 标准差={interp_data.std():.8f}")
    
    # 3. 插值误差统计
    print("\n3. 插值误差统计:")
    error_cols = ['base_time'] + acc_cols + ['angular_velocity_x (dps)', 'angular_velocity_y (dps)', 
                 'angular_velocity_z (dps)', 'temperature (°c)', 'longitude', 'latitude']
    
    for col in error_cols:
        if col in interpolated_df.columns:
            # 获取两个数据框中都有值的索引
            interp_valid = interpolated_df[col].dropna()
            
            if len(interp_valid) > 0:
                print(f"{col}:")
                print(f"  - 平均值: {interp_valid.mean():.8f}")
                print(f"  - 标准差: {interp_valid.std():.8f}")

if __name__ == "__main__":
    # 读取数据
    original_file = "test_data/mag_data.csv"
    interpolated_file = "merged_sensor_data.csv"
    
    if not Path(original_file).exists() or not Path(interpolated_file).exists():
        print(f"Error: 找不到数据文件 {original_file} 或 {interpolated_file}")
        exit(1)
    
    original_df = pd.read_csv(original_file)
    interpolated_df = pd.read_csv(interpolated_file)
    
    evaluate_interpolation(original_df, interpolated_df)
