import serial
import time

class MemoryBuffer:
    def __init__(self):
        self.buffer = []
    
    def write(self, data):
        self.buffer.append(data)
    
    def get_data(self):
        return ''.join(self.buffer)

def send_and_read_from_serial(port, baudrate, send_data1, send_data2):
    # 初始化串口连接
    ser = serial.Serial(port, baudrate, timeout=1)
    # 初始化 buffer
    buffer = MemoryBuffer()
    time.sleep(1.8)
    ser.write(send_data1.encode('ascii'))  # 发送 db 命令
    time.sleep(0.5)  # 等待设备回应
    # 等待串口初始化
    # 初始化 x, y, z 数组
    x_values = []
    y_values = []
    z_values = []
    t_values = []
    try:
        # 发送 rc 命令
        print("Sending 'rc' command...")
        ser.write(send_data2.encode('ascii'))  # 发送 rc 命令
        time.sleep(1.06)  # 等待设备回应
        
        # 等待接收数据
        if ser.in_waiting > 0:
            # 读取所有可用数据
            received_data = ser.read(ser.in_waiting).decode(errors='ignore')
            #print(f"Received raw data: '{received_data}'")  # 打印接收到的原始数据
            buffer.write(received_data)

            # 按换行符拆分数据
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
                                t=xyz_parts[0].strip()  # 时间戳
                                x = xyz_parts[1].strip()  # x值
                                y = xyz_parts[2].strip()  # y值
                                z = xyz_parts[3].strip()  # z值
                                # 将 x, y, z 添加到相应的数组中
                                t_values.append(t)
                                x_values.append(x)
                                y_values.append(y)
                                z_values.append(z)
                                #print(f"Extracted values - x: {x}, y: {y}, z: {z}")  # 提取值信息
    finally:
        # 关闭串口
        ser.close()   
    return buffer, x_values, y_values, z_values, t_values  # 返回 x, y, z 数组

# 示例使用
if __name__ == "__main__":

    port ="COM23" 
    baudrate = 115200
    send_data_rc = "rc"  # 需要先发送的命令
    
    send_data_db= "db 15"  
    # 等待串口初始化
    buffer, x_list, y_list, z_list, t_list = send_and_read_from_serial(port, baudrate, send_data_db, send_data_rc)
    timestamp = time.time()

# 转换为本地时间的结构化格式
    local_time = time.localtime(timestamp)

# 格式化为可读的字符串
    readable_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    print(f"script1 finished at time: {readable_time}")
    print(f"x values: {x_list}")
    print(f"y values: {y_list}")
    print(f"z values: {z_list}")
    print(f"t values: {t_list}")
    print(f"xlength: {len(x_list)}")
    print(f"ylength: {len(y_list)}")
    print(f"zlength: {len(z_list)}")
    print(f"tlength: {len(t_list)}")
   