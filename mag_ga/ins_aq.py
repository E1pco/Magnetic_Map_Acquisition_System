from mpl_toolkits.basemap import Basemap
import time
import os
import csv
from datetime import datetime
import platform
import argparse
import threading
import serial
from lib.device_model import DeviceModel
from lib.data_processor.roles.jy901s_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.wit_protocol_resolver import WitProtocolResolver
import matplotlib.pyplot as plt
# 初始化数据列表
chaptime_list = []
temp_list = []
accx_list = []
accy_list = []
accz_list = []
lon_list = []
lat_list = []
gyro_x_list = []
gyro_y_list = []
gyro_z_list = []

# 全局变量
_IsWriteF = False
csv_writer = None
csvfile = None
stop_event = threading.Event()

def log_message(message):
    """将消息同时输出到控制台和日志文件"""
    print(message)
    with open('mag_ga/ins_aq.log', 'a') as log_file:
        log_file.write(f'{datetime.now()}: {message}\n')

def readConfig(device):
    tVals = device.readReg(0x02, 3)
    if len(tVals) > 0:
        log_message("返回结果：" + str(tVals))
    else:
        log_message("无返回")
    tVals = device.readReg(0x23, 2)
    if len(tVals) > 0:
        log_message("返回结果：" + str(tVals))
    else:
        log_message("无返回")

def setConfig(device):
    device.unlock()
    time.sleep(0.1)
    device.writeReg(0x04, 6)
    time.sleep(0.1)
    device.writeReg(0x03, 9)
    time.sleep(0.1)
    device.writeReg(0x23, 0)
    time.sleep(0.1)
    device.writeReg(0x24, 0)
    time.sleep(0.1)
    device.save()

def AccelerationCalibration(device):
    device.AccelerationCalibration()
    log_message("加计校准结束")

def onUpdate_uesr(deviceModel):
    """
    数据更新事件
    :param deviceModel: 设备模型
    :return:
    """
    # 提取数据并存储到字典中
    sensor_data = {
        "芯片时间": deviceModel.getDeviceData("Chiptime"),
        "温度": deviceModel.getDeviceData("temperature"),
        "加速度": {
            "X轴": deviceModel.getDeviceData("accX"),
            "Y轴": deviceModel.getDeviceData("accY"),
            "Z轴": deviceModel.getDeviceData("accZ"),
        },
        "经度": deviceModel.getDeviceData("lon"),
        "纬度": deviceModel.getDeviceData("lat"),
        "角速度":{
            "X轴": deviceModel.getDeviceData("gyroX"),
            "Y轴": deviceModel.getDeviceData("gyroY"),
            "Z轴": deviceModel.getDeviceData("gyroZ"),
        }
        

    }

    chip_time = sensor_data["芯片时间"]
    temperature = sensor_data["温度"]
    acc_x = sensor_data["加速度"]["X轴"]
    acc_y = sensor_data["加速度"]["Y轴"]
    acc_z = sensor_data["加速度"]["Z轴"]
    lon = sensor_data["经度"]
    lat = sensor_data["纬度"]
    gyro_x = sensor_data["角速度"]["X轴"]
    gyro_y = sensor_data["角速度"]["Y轴"]
    gyro_z = sensor_data["角速度"]["Z轴"]

    # 将数据存储到全局列表
    global chaptime_list, temp_list, accx_list, accy_list, accz_list, lon_list, lat_list,gyro_x_list,gyro_y_list,gyro_z_list
    chaptime_list.append(chip_time)
    temp_list.append(temperature)
    accx_list.append(acc_x)
    accy_list.append(acc_y)
    accz_list.append(acc_z)
    lon_list.append(lon)
    lat_list.append(lat)
    gyro_x_list.append(gyro_x)
    gyro_y_list.append(gyro_y)
    gyro_z_list.append(gyro_z)

    if _IsWriteF:
        csv_writer.writerow([
            sensor_data["芯片时间"],
            sensor_data["加速度"]["X轴"],
            sensor_data["加速度"]["Y轴"],
            sensor_data["加速度"]["Z轴"],            
            sensor_data["角速度"]["X轴"],
            sensor_data["角速度"]["Y轴"],
            sensor_data["角速度"]["Z轴"],
            sensor_data["温度"],
            sensor_data["经度"],
            sensor_data["纬度"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        ])

def startRecord():
    """
    开始记录数据到CSV文件
    """
    global _IsWriteF, csv_writer, csvfile

    # 创建data文件夹（如果不存在）
    if not os.path.exists('ins_data'):
        os.makedirs('ins_data')
    
    # 新建一个CSV文件
    filename = os.path.join('ins_data', str(datetime.now().strftime('ins_data_%Y%m%d%H%M%S.%f')[:-3]) + ".csv")
    csvfile = open(filename, "w", newline='')
    _IsWriteF = True
    
    # 创建csv写入器
    csv_writer = csv.writer(csvfile)
    
    # 写入CSV标题行
    header = [
        "Chiptime", "Acceleration X (g)", "Acceleration Y (g)", "Acceleration Z (g)","Angular_velocity_X (dps)", "Angular_velocity_Y (dps)", "Angular_velocity_Z (dps)",
        "Temperature (°C)", "Longitude", "Latitude", "Record Time"
    ]
    csv_writer.writerow(header)

def endRecord():
    """
    结束记录数据
    """
    global _IsWriteF
    _IsWriteF = False
    csvfile.close()
    log_message("结束记录数据")

def visualize_data():
    """可视化加速度、温度及其他数据。"""
    # 创建主图
    fig = plt.figure(figsize=(14, 10))
    
    # 创建子图网格
    gs = fig.add_gridspec(3, 2)
    
    # 加速度图
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(chaptime_list, accx_list, label='Acceleration X', color='r')
    ax1.plot(chaptime_list, accy_list, label='Acceleration Y', color='g')
    ax1.plot(chaptime_list, accz_list, label='Acceleration Z', color='b')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Acceleration (g)')
    ax1.set_title('Acceleration Over Time')
    ax1.legend()
    ax1.grid()
    ax1.set_xticks([chaptime_list[0], chaptime_list[-1]])
    ax1.set_xticklabels([str(chaptime_list[0]), str(chaptime_list[-1])])

    # 温度图
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(chaptime_list, temp_list, label='Temperature', color='purple')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Temperature (°C)')
    ax2.set_title('Temperature Over Time')
    ax2.legend()
    ax2.grid()
    ax2.set_xticks([chaptime_list[0], chaptime_list[-1]])
    ax2.set_xticklabels([str(chaptime_list[0]), str(chaptime_list[-1])])

    # 角速度图
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(chaptime_list, gyro_x_list, label='Angular Velocity X', color='r')
    ax3.plot(chaptime_list, gyro_y_list, label='Angular Velocity Y', color='g')
    ax3.plot(chaptime_list, gyro_z_list, label='Angular Velocity Z', color='b')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Angular Velocity (dps)')
    ax3.set_title('Angular Velocity Over Time')
    ax3.legend()
    ax3.grid()
    ax3.set_xticks([chaptime_list[0], chaptime_list[-1]])
    ax3.set_xticklabels([str(chaptime_list[0]), str(chaptime_list[-1])])

    # 经纬度图
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(chaptime_list, lon_list, label='Longitude', color='orange')
    ax4.plot(chaptime_list, lat_list, label='Latitude', color='cyan')
    ax4.set_xlabel('Time (s)')
    ax4.set_ylabel('Coordinates')
    ax4.set_title('Position Over Time')
    ax4.legend()
    ax4.grid()
    ax4.set_xticks([chaptime_list[0], chaptime_list[-1]])
    ax4.set_xticklabels([str(chaptime_list[0]), str(chaptime_list[-1])])

    # 地图
    ax5 = fig.add_subplot(gs[2, :])
    m = Basemap(projection='merc', 
                llcrnrlat=min(lat_list)-0.1, urcrnrlat=max(lat_list)+0.1,
                llcrnrlon=min(lon_list)-0.1, urcrnrlon=max(lon_list)+0.1,
                resolution='h', ax=ax5)
    
    m.drawcoastlines()
    m.drawcountries()
    m.drawstates()
    m.fillcontinents(color='lightgreen', lake_color='aqua')
    m.drawmapboundary(fill_color='aqua')
    
    x, y = m(lon_list, lat_list)
    m.plot(x, y, 'ro-', markersize=5, linewidth=1)
    m.plot(x[0], y[0], 'go', markersize=8, label='Start')
    m.plot(x[-1], y[-1], 'bo', markersize=8, label='End')
    ax5.set_title('Trajectory Map')
    ax5.legend()

    plt.tight_layout()
    plt.show()

def wait_for_mag_ready():
    while True:
        try:
            with open("/dev/shm/mag_ready", "r") as f:
                content = f.read().strip()
                if content == "ready":
                    # 读取到ready后删除文件
                    os.remove("/dev/shm/mag_ready")
                    return
        except FileNotFoundError:
            time.sleep(0.1)

# Global timing variables
start_time = None
finish_time = None

def main(duration):
    """
    Main function to run the program for a specified duration
    :param duration: Duration to run the program in seconds
    """
    global start_time, finish_time
    
    # 初始化设备模型
    device = DeviceModel(
        "我的JY901",
        WitProtocolResolver(),
        JY901SDataProcessor(),
        "51_0"
    )
    if platform.system().lower() == 'linux':
        device.serialConfig.portName = "/dev/ttyUSB0"
    else:
        device.serialConfig.portName = "COM5"
    device.serialConfig.baud = 115200
    #wait_for_mag_ready()
    #time.sleep(2.24)

    device.openDevice()
    setConfig(device)
    start_time = datetime.now()
    log_message(f'ins_aq started: {start_time}')
    device.dataProcessor.onVarChanged.append(onUpdate_uesr)

    if duration != 0:
        startRecord()  # 开始记录数据到 CSV
        time.sleep(duration)
        device.closeDevice()
        endRecord()  # 结束记录数据
    else:
        startRecord()  # 开始记录数据到 CSV
        input()
        device.closeDevice()
        endRecord()  # 结束记录数据

    finish_time = datetime.now()
    log_message(f'ins_aq finished: {finish_time}')
    log_message("结束记录数据")
    
    # 计算并写入最后的消息
    elapsed_time = (finish_time - start_time).total_seconds()
    final_msg = f"数据采集完成\n开始时间: {start_time}\n结束时间: {finish_time}\n运行时间: {elapsed_time:.1f}秒"
    with open("/dev/shm/ins_final_msg", "w") as f:
        f.write(final_msg)

    visualize_data()  # 可视化数据

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run program for a specified duration.")
    parser.add_argument("duration", type=int, help="Duration to run the program in seconds")
    args = parser.parse_args()
    main(args.duration)
    print("程序运行时间：" + str(finish_time-start_time))
