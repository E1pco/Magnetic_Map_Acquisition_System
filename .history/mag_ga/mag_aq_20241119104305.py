import serial
import time
import threading
from datetime import datetime

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
        line = line.strip()  # 去除前后空白
        parts = line.split()  # 使用空格分割

        for i, part in enumerate(parts):
            if part.startswith("RD"):
                if i + 1 < len(parts):
                    # 对应格式 "RD a,b,c,d"
                    xyz_parts = parts[i + 1].split(",")  # 分割数据部分
                    if len(xyz_parts) == 4:  # 确保有4个部分
                        t = xyz_parts[0].strip()  # 时间戳
                        x = xyz_parts[1].strip()  # x值
                        y = xyz_parts[2].strip()  # y值
                        z = xyz_parts[3].strip()  # z值
                        # 将 x, y, z 添加到相应的数组中
                        t_values.append(t)
                        x_values.append(x)
                        y_values.append(y)
                        z_values.append(z)

    return x_values, y_values, z_values, t_values

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
        ser.write(send_data2.encode('ascii'))

        
        # 等待用户输入停止命令
        time.sleep(1)
        #input("Press Enter to stop reading...\n")
        stop_event.set()  # 设置停止事件，停止读取线程
    finally:
        reader.join()  # 等待读取线程结束
        ser.close()

    # 获取并解析数据
    received_data = buffer.get_data()
    x_list, y_list, z_list, t_list = parse_received_data(received_data)

    return x_list, y_list, z_list, t_list

# 示例使用
if __name__ == "__main__":
    port = "COM23"
    baudrate = 115200
    send_data_rc = "rc"
    send_data_db = "db 15"
    
    x_list, y_list, z_list, t_list = send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc)

    # 打印最终结果
    print("Data acquisition finished.")

    print(f"x values: {x_list}")
    print(f"y values: {y_list}")
    print(f"z values: {z_list}")
    print(f"t values: {t_list}")
    print(f"x length: {len(x_list)}")
    print(f"y length: {len(y_list)}")
    print(f"z length: {len(z_list)}")
    print(f"t length: {len(t_list)}")
