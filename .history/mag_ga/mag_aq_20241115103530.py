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

def send_and_read_from_serial(port, baudrate, send_data1, send_data2):
    ser = serial.Serial(port, baudrate, timeout=1)
    buffer = MemoryBuffer()
    time.sleep(1.8)
    ser.write(send_data1.encode('ascii'))
    time.sleep(0.5)

    # 创建停止事件
    stop_event = threading.Event()
    reader = SerialReader(ser, buffer, stop_event)

    reader.start()  # 启动读取线程

    try:
        print("Sending 'rc' command...")
        ser.write(send_data2.encode('ascii'))
        
        
        # 等待用户输入停止命令
        input("Press Enter to stop reading...\n")
        stop_event.set()  # 设置停止事件，停止读取线程
    finally:
        reader.join()  # 等待读取线程结束
        ser.close()

    return buffer.get_data()  # 返回读取的数据

# 示例使用
if __name__ == "__main__":
    port = "COM23"
    baudrate = 115200
    send_data_rc = "rc"
    send_data_db = "db 15"
    
    buffer_data = send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc)
    print("Received data:", buffer_data)
