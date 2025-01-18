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
def save_to_csv(file_path, t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes):
    """保存数据到CSV文件并进行处理"""
    # 创建DataFrame
    df = pd.DataFrame({
        'Time': [round(t, 6) for t in t_values],
        'X': [round(x, 6) for x in x_values],
        'Y': [round(y, 6) for y in y_values],
        'Z': [round(z, 6) for z in z_values],
        'Magnitude': [round(m, 6) for m in magnitudes],
        'Filtered Magnitude': [round(fm, 6) for fm in filtered_magnitudes]
    })
    
    # 处理数据
    df_processed, deleted_rows = process_mag_data(df)
    
    # 再次确保所有数值都是6位小数
    for col in ['Time', 'X', 'Y', 'Z', 'Magnitude', 'Filtered Magnitude']:
        df_processed[col] = df_processed[col].round(6)
    
    # 生成处理后的文件名
    base_name = os.path.splitext(file_path)[0]
    processed_file = f"{base_name}_processed.csv"
    
    # 保存处理后的数据，使用float_format确保输出6位小数
    df_processed.to_csv(processed_file, index=False, float_format='%.6f')
    
    # 同时保存原始数据，也使用6位小数
    df.to_csv(file_path, index=False, float_format='%.6f')
    
    print(f"原始数据已保存到: {file_path}")
    print(f"处理后的数据已保存到: {processed_file}")
    print(f"处理过程中合并了 {deleted_rows} 对数据点")

# 解析接收到的数据
def parse_received_data(received_data):
    x_values = []
    y_values = []
    z_values = []
    t_values = []

    lines = received_data.splitlines()

    for line in lines:
        line = line.strip()
        parts = line.split()

        for i, part in enumerate(parts):
            if part.startswith("RD"):
                if i + 1 < len(parts):
                    xyz_parts = parts[i + 1].split(",")
                    if len(xyz_parts) == 4:
                        t = xyz_parts[0].strip()
                        x = xyz_parts[1].strip()
                        y = xyz_parts[2].strip()
                        z = xyz_parts[3].strip()
                        t_values.append(float(t))  # 转换为浮点数以便绘图
                        x_values.append(float(x))
                        y_values.append(float(y))
                        z_values.append(float(z))
    
    return x_values, y_values, z_values, t_values

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

# 处理磁力计数据，合并时间间隔过小的数据点，保持时间不变
def process_mag_data(df):
    """处理磁力计数据，合并时间间隔过小的数据点，保持时间不变"""
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
                # 只对磁力计数据取平均值，时间保持不变
                for col in ['Time','X', 'Y', 'Z', 'Magnitude', 'Filtered Magnitude']:
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
    
    return df, len(rows_to_drop)

# 从串口读取数据
def read_from_serial(ser, stop_event, data_lists, duration):
    x_values, y_values, z_values, t_values = data_lists
    start_time = time.time()

    while not stop_event.is_set():
        try:
            if not ser.is_open:
                break
            if ser.in_waiting > 0:
                line = ser.readline().decode(errors='ignore').strip()
                if line and not stop_event.is_set():
                    x_new, y_new, z_new, t_new = parse_received_data(line)
                    if x_new and y_new and z_new and t_new:
                        x_values.extend(x_new)
                        y_values.extend(y_new)
                        z_values.extend(z_new)
                        t_values.extend(t_new)
            if duration != 0 and time.time() - start_time > duration:
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
        read_thread = threading.Thread(target=read_from_serial, args=(ser, stop_event, [x_values, y_values, z_values, t_values], duration))
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
        save_to_csv(output_csv_file, t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes)
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
        port = "/dev/mag"  # 根据实际情况修改
    
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
