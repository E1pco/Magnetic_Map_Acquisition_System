import serial
import time
import threading
from datetime import datetime
import matplotlib.pyplot as plt
import queue

class SerialReader(threading.Thread):
    def __init__(self, ser, plot_event, stop_event):
        super().__init__()
        self.ser = ser
        self.plot_event = plot_event
        self.stop_event = stop_event

    def run(self):
        received_data = ""
        while not self.stop_event.is_set():
            if self.ser.in_waiting > 0:
                # 读取数据并解码
                new_data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                received_data += new_data  # 不断累积数据
                # 解析数据
                x_list, y_list, z_list, t_list = parse_received_data(received_data)
                if len(t_list) > 0:  # 只在有数据时进行可视化
                    self.plot_event.put((x_list, y_list, z_list, t_list))
                # 清理已解析的数据
                received_data = ""  # 需要根据实际情况来清空或部分保留数据
                time.sleep(0.1)  # 防止占用过多 CPU

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

def send_and_read_from_serial(port, baudrate, send_data1, send_data2):
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(1.8)
    ser.write(send_data1.encode('ascii'))
    time.sleep(0.5)

    stop_event = threading.Event()
    plot_event = queue.Queue()
    reader = SerialReader(ser, plot_event, stop_event)
    reader.start()

    try:
        print("Sending 'rc' command...")
        time.sleep(0.1)
        ser.write(send_data2.encode('ascii'))
        now_start = datetime.now()
        current_time_start = now_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq started:", current_time_start)

        while not stop_event.is_set():
            if not plot_event.empty():
                x_list, y_list, z_list, t_list = plot_event.get()
                #visualize_data(x_list, y_list, z_list, t_list)

        time.sleep(1)  # 等待数据更为稳定
        stop_event.set()  # 设置停止事件，停止读取线程
    finally:
        reader.join()  # 等待读取线程结束
        ser.close()
        now_finish = datetime.now()
        current_time_finish = now_finish.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq finished:", current_time_finish)
        print("结束记录数据")

if __name__ == "__main__":
    port = "COM23"  # 根据实际情况修改
    baudrate = 115200
    send_data_rc = "rc"
    send_data_db = "db 15"
    send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc)
    
