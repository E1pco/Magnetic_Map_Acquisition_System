import serial
import time
from datetime import datetime
import matplotlib.pyplot as plt
import threading
import csv
import argparse
import os
import numpy as np
import pandas as pd

# 文件路径配置
UNPROCESSED_DATA_DIR = "mag_data/unprocessed"
PROCESSED_DATA_DIR = "mag_data/processed"

# 保存数据到CSV（只保留模值和滤波后的模值六位小数）
def save_to_csv(file_path, t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes, timestamps, duration):
    """保存数据到CSV文件并进行处理"""
    # 创建DataFrame
    df = pd.DataFrame({
        'Time': [round(t, 6) for t in t_values],
        'X': [round(x, 6) for x in x_values],
        'Y': [round(y, 6) for y in y_values],
        'Z': [round(z, 6) for z in z_values],
        'Magnitude': [round(m, 6) for m in magnitudes],
        'Filtered Magnitude': [round(fm, 6) for fm in filtered_magnitudes],
        'Timestamp': timestamps
    })
    
    # 保存原始数据
    os.makedirs(UNPROCESSED_DATA_DIR, exist_ok=True)
    base_name = os.path.basename(file_path)
    unprocessed_file = os.path.join(UNPROCESSED_DATA_DIR, base_name)
    df.to_csv(unprocessed_file, index=False, float_format='%.6f')
    print(f"原始数据已保存到: {unprocessed_file}")
    
    # 处理数据
    df_processed, _ = process_mag_data(df.copy())  # 使用df的副本进行处理
    
    # 再次确保所有数值都是6位小数
    for col in ['Time', 'X', 'Y', 'Z', 'Magnitude', 'Filtered Magnitude']:
        df_processed[col] = df_processed[col].round(6)
    
    # 删除原始时间戳列，然后将处理后的时间戳列重命名
    if 'Processed_Timestamp' in df_processed.columns:
        if 'Timestamp' in df_processed.columns:
            df_processed = df_processed.drop('Timestamp', axis=1)
        df_processed = df_processed.rename(columns={'Processed_Timestamp': 'Timestamp'})
    
    # 添加新列Base_Time，第一行保持原始时间戳，之后的行从第一个时间戳开始累加Time值
    base_timestamp = pd.to_datetime(df_processed['Timestamp'].iloc[0])
    first_time = df_processed['Time'].iloc[0]
    
    def calculate_base_time(row, index):
        if index == 0:
            return base_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return (base_timestamp + pd.Timedelta(seconds=float(row['Time'] - first_time))).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    df_processed['Base_Time'] = [calculate_base_time(row, i) for i, row in df_processed.iterrows()]
    
    # 确保列的顺序正确
    columns = ['Base_Time', 'Time', 'X', 'Y', 'Z', 'Magnitude', 'Filtered Magnitude', 'Timestamp']
    df_processed = df_processed[columns]
    
    # 过滤掉Time大于Duration的数据
    df_processed = df_processed[df_processed['Time'] <= duration]
    
    # 保存处理后的数据
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    processed_file = os.path.join(PROCESSED_DATA_DIR, base_name.replace(".csv", "_processed.csv"))
    df_processed.to_csv(processed_file, index=False, float_format='%.6f')
    print(f"处理后的数据已保存到: {processed_file}")

# 解析接收到的数据
def parse_received_data(received_data):
    x_values = []
    y_values = []
    z_values = []
    t_values = []
    timestamps = []
    
    lines = received_data.splitlines()
    
    # 用于时间戳处理的变量
    last_different_timestamp = None  # 上一个不同的时间戳
    same_timestamp_count = 0  # 相同时间戳的计数
    temp_data_points = []  # 临时存储具有相同时间戳的数据点
    
    for line in lines:
        line = line.strip()
        parts = line.split()
        
        for i, part in enumerate(parts):
            if part.startswith("RD"):
                if i + 1 < len(parts):
                    xyz_parts = parts[i + 1].split(",")
                    if len(xyz_parts) == 4:
                        t = float(xyz_parts[0].strip())
                        x = float(xyz_parts[1].strip())
                        y = float(xyz_parts[2].strip())
                        z = float(xyz_parts[3].strip())
                        
                        # 获取当前时间戳
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        
                        # 如果是第一个数据点
                        if not timestamps:
                            last_different_timestamp = current_time
                            timestamps.append(current_time)
                            t_values.append(t)
                            x_values.append(x)
                            y_values.append(y)
                            z_values.append(z)
                            continue
                        
                        # 检查与上一个时间戳的时间差
                        prev_timestamp = pd.to_datetime(timestamps[-1])
                        curr_timestamp = pd.to_datetime(current_time)
                        time_diff = (curr_timestamp - prev_timestamp).total_seconds() * 1000
                        
                        # 如果时间差小于2ms，认为是相同时间戳
                        if time_diff < 2:
                            same_timestamp_count += 1
                            temp_data_points.append({
                                't': t,
                                'x': x,
                                'y': y,
                                'z': z,
                                'timestamp': current_time
                            })
                        else:
                            # 如果之前有累积的相同时间戳数据点
                            if temp_data_points:
                                # 添加当前点到临时列表
                                temp_data_points.append({
                                    't': t,
                                    'x': x,
                                    'y': y,
                                    'z': z,
                                    'timestamp': current_time
                                })
                                
                                # 计算时间间隔
                                first_timestamp = pd.to_datetime(last_different_timestamp)
                                last_timestamp = pd.to_datetime(current_time)
                                total_interval = (last_timestamp - first_timestamp).total_seconds() * 1000
                                interval = total_interval / (len(temp_data_points))
                                
                                # 为临时列表中的每个点分配新的时间戳
                                for idx, point in enumerate(temp_data_points):
                                    new_timestamp = first_timestamp + pd.Timedelta(milliseconds=int(interval * (idx + 1)))
                                    timestamps.append(new_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
                                    t_values.append(point['t'])
                                    x_values.append(point['x'])
                                    y_values.append(point['y'])
                                    z_values.append(point['z'])
                                
                                # 清空临时列表和计数器
                                temp_data_points = []
                                same_timestamp_count = 0
                                last_different_timestamp = current_time
                            else:
                                # 正常添加数据点
                                timestamps.append(current_time)
                                t_values.append(t)
                                x_values.append(x)
                                y_values.append(y)
                                z_values.append(z)
                                last_different_timestamp = current_time
    
    # 处理最后剩余的临时数据点
    if temp_data_points:
        first_timestamp = pd.to_datetime(last_different_timestamp)
        last_timestamp = pd.to_datetime(temp_data_points[-1]['timestamp'])
        total_interval = (last_timestamp - first_timestamp).total_seconds() * 1000
        interval = total_interval / (len(temp_data_points))
        
        for idx, point in enumerate(temp_data_points):
            new_timestamp = first_timestamp + pd.Timedelta(milliseconds=int(interval * (idx + 1)))
            timestamps.append(new_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
            t_values.append(point['t'])
            x_values.append(point['x'])
            y_values.append(point['y'])
            z_values.append(point['z'])
    
    return x_values, y_values, z_values, t_values, timestamps

# 计算模值 (Magnitude)
def calculate_magnitude(x_values, y_values, z_values):
    magnitudes = np.sqrt(np.array(x_values)**2 + np.array(y_values)**2 + np.array(z_values)**2)
    return magnitudes

# 均值滤波，每10个数据点做一次均值
def moving_average_filter(data, window_size=10):
    filtered_data = []
    for i in range(len(data)):
        # 获取当前窗口的起始和结束索引
        start_index = max(0, i - window_size + 1)
        window = data[start_index:i+1]
        # 计算当前窗口的均值
        filtered_data.append(np.mean(window))
    return filtered_data

# 可视化数据
def visualize_data(x_values, y_values, z_values, t_values, magnitudes, filtered_magnitudes):
    plt.figure(figsize=(15, 8))

    # X, Y, Z Values Plot
    plt.subplot(2, 3, 1)
    plt.plot(t_values, x_values, label='X Values', color='r')
    plt.xlabel('Time (s)')
    plt.ylabel('X Values')
    plt.title('X Values Over Time')
    plt.grid()

    plt.subplot(2, 3, 2)
    plt.plot(t_values, y_values, label='Y Values', color='g')
    plt.xlabel('Time (s)')
    plt.ylabel('Y Values')
    plt.title('Y Values Over Time')
    plt.grid()

    plt.subplot(2, 3, 3)
    plt.plot(t_values, z_values, label='Z Values', color='b')
    plt.xlabel('Time (s)')
    plt.ylabel('Z Values')
    plt.title('Z Values Over Time')
    plt.grid()

    # Magnitudes Plot
    plt.subplot(2, 3, 4)
    plt.plot(t_values, magnitudes, label='Magnitude', color='purple')
    plt.xlabel('Time (s)')
    plt.ylabel('Magnitude')
    plt.title('Magnitude Over Time')
    plt.grid()

    # Filtered Magnitudes Plot
    plt.subplot(2, 3, 5)
    plt.plot(t_values, filtered_magnitudes, label='Filtered Magnitude', color='orange')
    plt.xlabel('Time (s)')
    plt.ylabel('Filtered Magnitude')
    plt.title('Filtered Magnitude Over Time')
    plt.grid()

    plt.tight_layout()
    plt.show()
    print()

# 处理磁力计数据，处理时间戳
def process_mag_data(df):
    """处理磁力计数据，处理时间戳，保留原始数据"""
    if len(df) < 2:
        return df, 0

    # 创建新的时间戳列，复制原始时间戳
    df['Processed_Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # 第一步：处理小于2ms的时间差，使用上一个时间戳
    i = 1
    while i < len(df):
        time_diff = (df.iloc[i]['Processed_Timestamp'] - df.iloc[i-1]['Processed_Timestamp']).total_seconds() * 1000
        if time_diff < 2:
            df.at[i, 'Processed_Timestamp'] = df.iloc[i-1]['Processed_Timestamp']
        i += 1
    
    # 第二步：在不同时间戳之间平均分配时间差
    i = 0
    while i < len(df):
        # 找到当前时间戳组的起始位置
        start_idx = i
        current_timestamp = df.iloc[i]['Processed_Timestamp']
        
        # 找到下一个不同的时间戳
        next_diff_idx = i + 1
        while next_diff_idx < len(df) and df.iloc[next_diff_idx]['Processed_Timestamp'] == current_timestamp:
            next_diff_idx += 1
            
        # 如果找到了下一个不同的时间戳
        if next_diff_idx < len(df):
            next_timestamp = df.iloc[next_diff_idx]['Processed_Timestamp']
            # 计算时间差（毫秒）
            time_diff = (next_timestamp - current_timestamp).total_seconds() * 1000
            # 需要分配的间隔数
            intervals = next_diff_idx - start_idx
            # 计算每个间隔的时间差
            interval_diff = time_diff / intervals if intervals > 0 else 0
            
            # 更新中间的时间戳
            for j in range(start_idx + 1, next_diff_idx):
                steps = j - start_idx
                new_timestamp = current_timestamp + pd.Timedelta(milliseconds=int(interval_diff * steps))
                df.at[j, 'Processed_Timestamp'] = new_timestamp
            
            i = next_diff_idx
        else:
            # 已经处理到最后一组时间戳
            break
    
    # 将处理后的时间戳转换回字符串格式
    df['Processed_Timestamp'] = df['Processed_Timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
    
    return df, 0

# 从串口读取数据
def read_from_serial(ser, stop_event, data_lists, duration):
    x_values, y_values, z_values, t_values, timestamps = data_lists
    start_time = time.time()

    while not stop_event.is_set():
        try:
            if not ser.is_open:
                break
            if ser.in_waiting > 0:
                line = ser.readline().decode(errors='ignore').strip()
                if line and not stop_event.is_set():
                    x_new, y_new, z_new, t_new, ts_new = parse_received_data(line)
                    if x_new and y_new and z_new and t_new and ts_new:
                        x_values.extend(x_new)
                        y_values.extend(y_new)
                        z_values.extend(z_new)
                        t_values.extend(t_new)
                        timestamps.extend(ts_new)
            # 修改时间判断逻辑，确保至少采集满指定时长
            if duration != 0 and time.time() - start_time >= duration + 0.15:  # 增加0.5秒的缓冲时间
                stop_event.set()
        except:
            break

def send_and_read_from_serial(port, baudrate, send_data1, send_data2, duration, output_csv_file):
    ser = None
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(1.8)
        ser.write(send_data1.encode('ascii'))
        time.sleep(0.5)

        x_values = []
        y_values = []
        z_values = []
        t_values = []
        timestamps = []
        stop_event = threading.Event()

        time.sleep(0.1)
        ser.write(send_data2.encode('ascii'))
        
        # 创建标记文件表示MAG已经准备就绪
        with open("/dev/shm/mag_ready", "w") as f:
            f.write("ready")
            
        now_start = datetime.now()
        current_time_start = now_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq started:", current_time_start)

        # 启动读取数据的线程
        read_thread = threading.Thread(target=read_from_serial, args=(ser, stop_event, [x_values, y_values, z_values, t_values, timestamps], duration))
        read_thread.start()

        # 在主线程中监听用户输入
        if duration == 0:
            try:
                while not stop_event.is_set():
                    user_input = input()  # 等待用户输入
                    stop_event.set()  # 当用户按下回车键时设置停止标志位
                    print("停止数据采集...")
            except KeyboardInterrupt:
                stop_event.set()
                print("程序被用户中断，停止数据采集...")

        # 等待读取线程结束
        read_thread.join()
        print("数据采集已停止。")

        now_finish = datetime.now()
        current_time_finish = now_finish.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq finished:", current_time_finish)
        print("结束记录数据")

        # 计算模值和均值滤波
        magnitudes = calculate_magnitude(x_values, y_values, z_values)
        filtered_magnitudes = moving_average_filter(magnitudes, window_size=10)
        
        # 保存数据到 CSV 文件
        save_to_csv(output_csv_file, t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes, timestamps, duration)
        visualize_data(x_values, y_values, z_values, t_values, magnitudes, filtered_magnitudes)
    finally:
        if ser is not None and ser.is_open:
            try:
                ser.close()
                ser = None  # 关闭后置为None
            except:
                pass

# 主函数
def main(duration):
    # 根据操作系统选择端口
    if os.name == 'nt':  # Windows 系统
        port = "COM6"  # 根据实际情况修改
    else:  # 假设其他系统为Linux
        port = "/dev/ttyUSB2"  # 根据实际情况修改
    
    baudrate = 115200
    send_data_rc = "rc"
    send_data_db = "db 15"
    
    # 创建必要的目录
    os.makedirs(UNPROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # 获取当前时间并格式化为字符串
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv_file = os.path.join(UNPROCESSED_DATA_DIR, f"mag_data_{current_time}.csv")
    
    # 启动数据采集
    send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc, duration, output_csv_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run program for a specified duration.")
    parser.add_argument("duration", type=int, help="Duration to run the program in seconds")
    args = parser.parse_args()
    main(args.duration)
