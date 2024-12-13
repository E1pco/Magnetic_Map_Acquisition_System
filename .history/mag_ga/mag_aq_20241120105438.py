import serial
import time
import threading
from datetime import datetime
import matplotlib.pyplot as plt

event = threading.Event()

class MemoryBuffer:
    def __init__(self):
        self.buffer = []
    
    def write(self, data):
        self.buffer.append(data)
    
    def get_data(self):
        return ''.join(self.buffer)

class SerialReader(threading.Thread):
    def __init__(self, ser, buffer, stop_event):
        super().__init__()
        self.ser = ser
        self.buffer = buffer
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            if self.ser.in_waiting > 0:
                received_data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                self.buffer.write(received_data)
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

class DataProcessor(threading.Thread):
    def __init__(self, buffer):
        super().__init__()
        self.buffer = buffer

    def run(self):
        # 获取并解析数据
        received_data = self.buffer.get_data()
        x_list, y_list, z_list, t_list = parse_received_data(received_data)

        # 可视化数据
        visualize_data(x_list, y_list, z_list, t_list)

def visualize_data(x_values, y_values, z_values, t_values):
    # 绘制 x, y, z 对应的时间 t 图
    plt.figure(figsize=(15, 5))

    # 绘制 x vs t
    plt.subplot(1, 3, 1)
    plt.plot(t_values, x_values, label='X Values', color='r')
    plt.xlabel('Time (s)')
    plt.ylabel('X Values')
    plt.title('X Values Over Time')
    plt.grid()

    # 绘制 y vs t
    plt.subplot(1, 3, 2)
    plt.plot(t_values, y_values, label='Y Values', color='g')
    plt.xlabel('Time (s)')
    plt.ylabel('Y Values')
    plt.title('Y Values Over Time')
    plt.grid()

    # 绘制 z vs t
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
    buffer = MemoryBuffer()
    time.sleep(1.8)
    ser.write(send_data1.encode('ascii'))
    time.sleep(0.5)

    stop_event = threading.Event()
    reader = SerialReader(ser, buffer, stop_event)

    reader.start()  # 启动读取线程

    try:
        print("Sending 'rc' command...")
        time.sleep(0.1)
        ser.write(send_data2.encode('ascii'))
        now_start = datetime.now()
        current_time_start = now_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq started:", current_time_start)

        time.sleep(1)  # 等待1秒
        stop_event.set()  # 设置停止事件，停止读取线程
    finally:
        reader.join()  # 等待读取线程结束
        ser.close()
        now_finish = datetime.now()
        current_time_finish = now_finish.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq finished:", current_time_finish)
        print("结束记录数据")

    # 启动数据处理线程
    processor = DataProcessor(buffer)
    processor.start()  # 启动数据处理线程
    processor.join()  # 等待数据处理线程结束

if __name__ == "__main__":
    port = "COM23"  # 根据实际情况修改
    baudrate = 115200
    send_data_rc = "rc"
    send_data_db = "db 15"
    
    send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc)
