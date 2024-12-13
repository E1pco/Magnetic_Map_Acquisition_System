import time
import os
import csv
from datetime import datetime
import platform
import argparse
from lib.device_model import DeviceModel
from lib.data_processor.roles.jy901s_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.wit_protocol_resolver import WitProtocolResolver

# 初始化数据列表
chaptime_list = []
temp_list = []
accx_list = []
accy_list = []
accz_list = []
lon_list = []
lat_list = []
def readConfig(device):
    tVals = device.readReg(0x02, 3)
    if len(tVals) > 0:
        print("返回结果：" + str(tVals))
    else:
        print("无返回")
    tVals = device.readReg(0x23, 2)
    if len(tVals) > 0:
        print("返回结果：" + str(tVals))
    else:
        print("无返回")

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
    print("加计校准结束")

def FiledCalibration(device):
    device.BeginFiledCalibration()
    if input("请分别绕XYZ轴慢速转动一圈，三轴转圈完成后，结束校准（Y/N)？").lower() == "y":
        device.EndFiledCalibration()
        print("结束磁场校准")
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
    }

   
    chip_time = sensor_data["芯片时间"]
    temperature = sensor_data["温度"]
    acc_x = sensor_data["加速度"]["X轴"]
    acc_y = sensor_data["加速度"]["Y轴"]
    acc_z = sensor_data["加速度"]["Z轴"]
    lon = sensor_data["经度"]
    lat = sensor_data["纬度"]
    
    # 将数据存储到全局列表
    global chaptime_list, temp_list, accx_list, accy_list, accz_list, lon_list, lat_list
    chaptime_list.append(chip_time)
    temp_list.append(temperature)
    accx_list.append(acc_x)
    accy_list.append(acc_y)
    accz_list.append(acc_z)
    lon_list.append(lon)
    lat_list.append(lat)

def startRecord():
    """
    开始记录数据到CSV文件
    """
    global _IsWriteF, csv_writer, csvfile

    # 创建data文件夹（如果不存在）
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 新建一个CSV文件
    filename = os.path.join('data', str(datetime.now().strftime('%Y%m%d%H%M%S')) + ".csv")
    csvfile = open(filename, "w", newline='')
    _IsWriteF = True
    
    # 创建csv写入器
    csv_writer = csv.writer(csvfile)
    
    # 写入CSV标题行
    header = [
        "Chiptime", "Acceleration X (g)", "Acceleration Y (g)", "Acceleration Z (g)",
        "Temperature (°C)", "Longitude", "Latitude"
    ]
    csv_writer.writerow(header)

def endRecord():
    """
    结束记录数据
    """
    global _IsWriteF, csvfile
    _IsWriteF = False
    csvfile.close()
    print("结束记录数据")

def visualize_data():
    """可视化加速度、温度及其他数据。"""
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 8))  # 调整图形大小

    # 绘制加速度
    plt.subplot(2, 2, 1)
    plt.plot(chaptime_list, accx_list, label='Acceleration X', color='r')
    plt.plot(chaptime_list, accy_list, label='Acceleration Y', color='g')
    plt.plot(chaptime_list, accz_list, label='Acceleration Z', color='b')
    plt.xlabel('Time (s)')
    plt.ylabel('Acceleration (g)')
    plt.title('Acceleration Over Time')
    plt.legend()
    plt.grid()
    
    # 优化横轴刻度显示
    plt.xticks([chaptime_list[0], chaptime_list[-1]], [str(chaptime_list[0]), str(chaptime_list[-1])])

    # 绘制温度变化
    plt.subplot(2, 2, 2)
    plt.plot(chaptime_list, temp_list, label='Temperature', color='purple')
    plt.xlabel('Time (s)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature Over Time')
    plt.legend()
    plt.grid()

    # 优化横轴刻度显示
    plt.xticks([chaptime_list[0], chaptime_list[-1]], [str(chaptime_list[0]), str(chaptime_list[-1])])

    # 绘制经度
    plt.subplot(2, 2, 3)
    plt.plot(chaptime_list, lon_list, label='Longitude', color='orange')
    plt.xlabel('Time (s)')
    plt.ylabel('Longitude')
    plt.title('Longitude Over Time')
    plt.legend()
    plt.grid()

    # 优化横轴刻度显示
    plt.xticks([chaptime_list[0], chaptime_list[-1]], [str(chaptime_list[0]), str(chaptime_list[-1])])

    # 绘制纬度
    plt.subplot(2, 2, 4)
    plt.plot(chaptime_list, lat_list, label='Latitude', color='cyan')
    plt.xlabel('Time (s)')
    plt.ylabel('Latitude')
    plt.title('Latitude Over Time')
    plt.legend()
    plt.grid()

    # 优化横轴刻度显示
    plt.xticks([chaptime_list[0], chaptime_list[-1]], [str(chaptime_list[0]), str(chaptime_list[-1])])

    plt.tight_layout()
    plt.show()


def main(duration):
    """
    Main function to run the program for a specified duration
    :param duration: Duration to run the program in seconds
    """
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
        device.serialConfig.portName = "COM13"
    device.serialConfig.baud = 115200
    time.sleep(2.397)
   
    device.openDevice()
    setConfig(device)
    now_start = datetime.now()
    current_time_start = now_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print("ins_aq started:", current_time_start)
    device.dataProcessor.onVarChanged.append(onUpdate_uesr)
    
    startRecord()  # 开始记录数据到 CSV
    time.sleep(duration)
    
    device.closeDevice()
    endRecord()  # 结束记录数据
    
    now_finish = datetime.now()
    current_time_finish = now_finish.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print("ins_aq finished:", current_time_finish)
    print("结束记录数据")    
    
    visualize_data()  # 可视化数据

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run program for a specified duration.")
    parser.add_argument("duration", type=int, help="Duration to run the program in seconds")
    args = parser.parse_args()
    main(args.duration)
