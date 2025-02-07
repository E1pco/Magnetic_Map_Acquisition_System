import pandas as pd

# 读取CSV文件
df = pd.read_csv('merged_sensor_data.csv')

# 检查每一行是否有空值
complete_data = df.dropna()

# 保存清理后的数据
complete_data.to_csv('merged_sensor_data.csv', index=False)

print(f"原始数据行数: {len(df)}")
print(f"清理后数据行数: {len(complete_data)}")
print(f"删除的行数: {len(df) - len(complete_data)}")
