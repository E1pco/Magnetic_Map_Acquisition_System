import serial
import time
from datetime import datetime
import matplotlib.pyplot as plt
import threading
import csv
import argparse

def save_to_csv(file_path, t_values, x_values, y_values, z_values):
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "X", "Y", "Z"])
        for t, x, y, z in zip(t_values, x_values, y_values, z_values):
            writer.writerow([t, x, y, z])

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

def visualize_data(x_values, y_values, z_values, t_values):
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    plt.plot(t_values, x_values, label='X Values', color='r')
    plt.xlabel('Time (s)')
    plt.ylabel('X Values')
    plt.title('X Values Over Time')
    plt.grid()

    plt.subplot(1, 3, 2)
    plt.plot(t_values, y_values, label='Y Values', color='g')
    plt.xlabel('Time (s)')
    plt.ylabel('Y Values')
    plt.title('Y Values Over Time')
    plt.grid()

    plt.subplot(1, 3, 3)
    plt.plot(t_values, z_values, label='Z Values', color='b')
    plt.xlabel('Time (s)')
    plt.ylabel('Z Values')
    plt.title('Z Values Over Time')
    plt.grid()

    plt.tight_layout()
    plt.show()

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

        # 保存数据到 CSV 文件
        save_to_csv(output_csv_file, t_values, x_values, y_values, z_values)

        # 在收集完所有数据后进行可视化
        visualize_data(x_values, y_values, z_values, t_values)

    finally:
        ser.close()

def main(duration):
    port = "COM6"  # 根据实际情况修改
    baudrate = 115200
    send_data_rc = "rc"
    send_data_db = "db 15"
    
    # 设置输出文件路径
    output_csv_file = "output_data.csv"  # 设置输出的 CSV 文件路径
    
    # 启动数据采集
    send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc, duration, output_csv_file)
    print(f"Program ran for {duration} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run program for a specified duration.")
    parser.add_argument("duration", type=int, help="Duration to run the program in seconds")
    args = parser.parse_args()
    
    main(args.duration)
