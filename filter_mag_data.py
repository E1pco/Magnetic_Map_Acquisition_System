import pandas as pd

# 读取CSV文件
df = pd.read_csv('merged_sensor_data.csv')

# 将timestamp列转换为datetime类型
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 找到第一个磁力计数据不为空的时间点
start_time = df[df['time'].notna()]['timestamp'].iloc[0]

# 只保留该时间点之后的数据
filtered_df = df[df['timestamp'] >= start_time]

# 保存过滤后的数据
filtered_df.to_csv('filtered_mag_data.csv', index=False)

print(f"已过滤数据，只保留 {start_time} 之后的记录")
print(f"原始数据行数: {len(df)}")
print(f"过滤后数据行数: {len(filtered_df)}")
