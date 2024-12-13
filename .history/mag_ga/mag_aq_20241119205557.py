import serial
import time
import threading
from datetime import datetime
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
        time.sleep(0.1)
        ser.write(send_data2.encode('ascii'))
        now_start = datetime.now()
        current_time_start = now_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq started:", current_time_start)
        #set_flag()  # 设置事件
        # 启动线程来设置事件
        #flag_thread = threading.Thread(target=set_flag)
        #flag_thread.start()

        time.sleep(10)  # 等待1秒
        stop_event.set()  # 设置停止事件，停止读取线程
    finally:
        reader.join()  # 等待读取线程结束
        ser.close()
        now_finish = datetime.now()
        current_time_finish = now_finish.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("mag_aq finished:", current_time_finish)
        print("结束记录数据")

    # 获取并解析数据
    received_data = buffer.get_data()
    x_list, y_list, z_list, t_list = parse_received_data(received_data)

    return x_list, y_list, z_list, t_list

def set_flag():
    event.set()  # 设置事件

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
