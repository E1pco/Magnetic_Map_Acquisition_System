import serial
import time
from datetime import datetime
import matplotlib.pyplot as plt
import threading
import csv
import argparse
import os
import numpy as np

# 保存数据到CSV（只保留模值和滤波后的模值六位小数）
def save_to_csv(file_path, t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "X", "Y", "Z", "Magnitude", "Filtered Magnitude"])
        for t, x, y, z, m, fm in zip(t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes):
            # 仅对模值和滤波后的模值保留六位小数
            writer.writerow([t, x, y, z, round(m, 6), round(fm, 6)])

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
# 从串口读取数据
def read_from_serial(ser, stop_event, data_lists, duration):
    x_values, y_values, z_values, t_values = data_lists
    start_time = time.time()

    try:
        while not stop_event.is_set():
            if ser.in_waiting > 0:
                new_data = ser.read(ser.in_waiting).decode(errors='ignore')
                x_new, y_new, z_new, t_new = parse_received_data(new_data)
                x_values.extend(x_new)
                y_values.extend(y_new)
                z_values.extend(z_new)
                t_values.extend(t_new)

            # 如果超过指定的持续时间，则停止读取数据
            if time.time() - start_time > duration:
                stop_event.set()

            time.sleep(0.1)
    except Exception as e:
        print(f"Error in read_from_serial thread: {e}")

# 发送和读取串口数据
def send_and_read_from_serial(port, baudrate, send_data1, send_data2, duration, output_csv_file):
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(1.8)
    ser.write(send_data1.encode('ascii'))
    time.sleep(0.5)

    x_values = []
    y_values = []
    z_values = []
    t_values = []
    stop_event = threading.Event()

    try:
        print("Sending 'rc' command...")
        time.sleep(0.1)
        ser.write(send_data2.encode('ascii'))
        now_start = datetime.now()
        current_time_start = now_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq started:", current_time_start)

        # 启动读取数据的线程
        read_thread = threading.Thread(target=read_from_serial, args=(ser, stop_event, [x_values, y_values, z_values, t_values], duration))
        read_thread.start()

        # 等待读取线程结束
        read_thread.join()
        print("Stopping data collection...")

        now_finish = datetime.now()
        current_time_finish = now_finish.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq finished:", current_time_finish)
        print("结束记录数据")

        # 计算模值和均值滤波
        magnitudes = calculate_magnitude(x_values, y_values, z_values)
        filtered_magnitudes = moving_average_filter(magnitudes, window_size=10)

        # 保存数据到 CSV 文件
        save_to_csv(output_csv_file, t_values, x_values, y_values, z_values, magnitudes, filtered_magnitudes)

        # 在收集完所有数据后进行可视化
        visualize_data(x_values, y_values, z_values, t_values, magnitudes, filtered_magnitudes)

    finally:
        ser.close()

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
    if not os.path.exists('mag_data'):
        os.makedirs('mag_data')   
    # 获取当前时间并格式化为字符串
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv_file = f"mag_data/mag_data_{current_time}.csv"  # 设置输出的 CSV 文件路径，文件名为当前时间
    
    # 启动数据采集
    send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc, duration, output_csv_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run program for a specified duration.")
    parser.add_argument("duration", type=int, help="Duration to run the program in seconds")
    args = parser.parse_args()
    
    main(args.duration)