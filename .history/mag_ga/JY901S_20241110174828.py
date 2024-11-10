# coding:UTF-8
"""
    测试文件
    Test file
"""
import time
import datetime
import platform
import struct
import lib.device_model as deviceModel
from lib.data_processor.roles.jy901s_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.wit_protocol_resolver import WitProtocolResolver
import os
welcome = """
欢迎使用维特智能示例程序    Welcome to the Wit-Motoin sample program
"""
_writeF = None                    #写文件  Write file
_IsWriteF = False                 #写文件标识    Write file identification
chaptime_list=[]
temp_list=[]
accx_list=[]
accy_list=[]
accz_list=[]
anglex_list=[]
angley_list=[]
anglez_list=[]
lon_list=[]
lat_list=[]
yaw_list=[]
speed_list=[]
def readConfig(device):
    """
    读取配置信息示例    Example of reading configuration information
    :param device: 设备模型 Device model
    :return:
    """
    tVals = device.readReg(0x02,3)  #读取数据内容、回传速率、通讯速率   Read data content, return rate, communication rate
    if (len(tVals)>0):
        print("返回结果：" + str(tVals))
    else:
        print("无返回")
    tVals = device.readReg(0x23,2)  #读取安装方向、算法  Read the installation direction and algorithm
    if (len(tVals)>0):
        print("返回结果：" + str(tVals))
    else:
        print("无返回")

def setConfig(device):
    """
    设置配置信息示例    Example setting configuration information
    :param device: 设备模型 Device model
    :return:
    """
    device.unlock()                # 解锁 unlock
    time.sleep(0.1)                # 休眠100毫秒    Sleep 100ms
    device.writeReg(0x03, 6)       # 设置回传速率为10HZ    Set the transmission back rate to 10HZ
    time.sleep(0.1)                # 休眠100毫秒    Sleep 100ms
    device.writeReg(0x23, 0)       # 设置安装方向:水平、垂直   Set the installation direction: horizontal and vertical
    time.sleep(0.1)                # 休眠100毫秒    Sleep 100ms
    device.writeReg(0x24, 0)       # 设置安装方向:九轴、六轴   Set the installation direction: nine axis, six axis
    time.sleep(0.1)                # 休眠100毫秒    Sleep 100ms
    device.save()                  # 保存 Save

def AccelerationCalibration(device):
    """
    加计校准    Acceleration calibration
    :param device: 设备模型 Device model
    :return:
    """
    device.AccelerationCalibration()                 # Acceleration calibration
    print("加计校准结束")

def FiledCalibration(device):
    """
    磁场校准    Magnetic field calibration
    :param device: 设备模型 Device model
    :return:
    """
    device.BeginFiledCalibration()                   # 开始磁场校准   Starting field calibration
    if input("请分别绕XYZ轴慢速转动一圈，三轴转圈完成后，结束校准（Y/N)？").lower()=="y":
        device.EndFiledCalibration()                 # 结束磁场校准   End field calibration
        print("结束磁场校准")

def onUpdate(deviceModel):
    """
    数据更新事件  Data update event
    :param deviceModel: 设备模型    Device model
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
        "角速度": {
            "X轴": deviceModel.getDeviceData("gyroX"),
            "Y轴": deviceModel.getDeviceData("gyroY"),
            "Z轴": deviceModel.getDeviceData("gyroZ"),
        },
        "角度": {
            "X轴": deviceModel.getDeviceData("angleX"),
            "Y轴": deviceModel.getDeviceData("angleY"),
            "Z轴": deviceModel.getDeviceData("angleZ"),
        },
        "磁场": {
            "X轴": deviceModel.getDeviceData("magX"),
            "Y轴": deviceModel.getDeviceData("magY"),
            "Z轴": deviceModel.getDeviceData("magZ"),
        },
        "经度": deviceModel.getDeviceData("lon"),
        "纬度": deviceModel.getDeviceData("lat"),
        "航向角": deviceModel.getDeviceData("Yaw"),
        "地速": deviceModel.getDeviceData("Speed"),
        "四元数": {
            "q1": deviceModel.getDeviceData("q1"),
            "q2": deviceModel.getDeviceData("q2"),
            "q3": deviceModel.getDeviceData("q3"),
            "q4": deviceModel.getDeviceData("q4"),
        }
    }
    
    # 单独提取每个值
    chip_time = sensor_data["芯片时间"]
    temperature = sensor_data["温度"]
    acc_x = sensor_data["加速度"]["X轴"]
    acc_y = sensor_data["加速度"]["Y轴"]
    acc_z = sensor_data["加速度"]["Z轴"]
    gyro_x = sensor_data["角速度"]["X轴"]
    gyro_y = sensor_data["角速度"]["Y轴"]
    gyro_z = sensor_data["角速度"]["Z轴"]
    angle_x = sensor_data["角度"]["X轴"]
    angle_y = sensor_data["角度"]["Y轴"]
    angle_z = sensor_data["角度"]["Z轴"]
    mag_x = sensor_data["磁场"]["X轴"]
    mag_y = sensor_data["磁场"]["Y轴"]
    mag_z = sensor_data["磁场"]["Z轴"]
    lon = sensor_data["经度"]
    lat = sensor_data["纬度"]
    yaw = sensor_data["航向角"]
    speed = sensor_data["地速"]
    q1 = sensor_data["四元数"]["q1"]
    q2 = sensor_data["四元数"]["q2"]
    q3 = sensor_data["四元数"]["q3"]
    q4 = sensor_data["四元数"]["q4"]
    global chaptime_list,temp_list,accx_list,accy_list,accz_list,anglex_list,angley_list,anglez_list,lon_list,lat_list,yaw_list,speed_list
    chaptime_list.append(chip_time)
    temp_list.append(temperature)
    accx_list.append(acc_x)
    accy_list.append(acc_y)
    accz_list.append(acc_z)
    anglex_list.append(angle_x)
    angley_list.append(angle_y)
    anglez_list.append(angle_z)
    lon_list.append(lon)
    lat_list.append(lat)
    yaw_list.append(yaw)
    speed_list.append(speed)
    print("传感器数据更新:")
    print(f"芯片时间: {chip_time}")
    print(f"温度: {temperature}")
    print(f"加速度: X轴={acc_x}, Y轴={acc_y}, Z轴={acc_z}")
    print(f"角速度: X轴={gyro_x}, Y轴={gyro_y}, Z轴={gyro_z}")
    print(f"角度: X轴={angle_x}, Y轴={angle_y}, Z轴={angle_z}")
    print(f"磁场: X轴={mag_x}, Y轴={mag_y}, Z轴={mag_z}")
    print(f"经度: {lon}")
    print(f"纬度: {lat}")
    print(f"航向角: {yaw}")
    print(f"地速: {speed}")
    print(f"四元数: q1={q1}, q2={q2}, q3={q3}, q4={q4}")
    print("-----------")

    
def dataRecord(deviceModel):
    """
    数据记录    Data recording
    :return:
    """
    global chaptime_list,temp_list,accx_list,accy_list,accz_list,anglex_list,angley_list,anglez_list,lon_list,lat_list,yaw_list,speed_list
    chaptime_list.append(deviceModel.getDeviceData("Chiptime"))
    temp_list.append(deviceModel.getDeviceData("temperature"))
    accx_list.append(deviceModel.getDeviceData("accX"))
    accy_list.append(deviceModel.getDeviceData("accY"))
    accz_list.append(deviceModel.getDeviceData("accZ"))
    anglex_list.append(deviceModel.getDeviceData("angleX"))
    angley_list.append(deviceModel.getDeviceData("angleY"))
    anglez_list.append(deviceModel.getDeviceData("angleZ"))
    lon_list.append(deviceModel.getDeviceData("lon"))
    lat_list.append(deviceModel.getDeviceData("lat"))
    yaw_list.append(deviceModel.getDeviceData("Yaw"))
    speed_list.append(deviceModel.getDeviceData("Speed"))
    time.sleep(1)  # 等待1秒钟进行数据记录
    endRecord()  # 结束记录数据
    return chaptime_list,temp_list,accx_list,accy_list,accz_list,anglex_list,angley_list,anglez_list,lon_list,lat_list,yaw_list,speed_list
     
def startRecord():
    """
    开始记录数据  Start recording d
    :return:
    """
    global _writeF
    global _IsWriteF
    
    # 创建data文件夹（如果不存在）
    if not os.path.exists('data'):
        os.makedirs('data')  # 创建数据文件夹
    
    # 新建一个文件
    filename = os.path.join('data', str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + ".txt")
    _writeF = open(filename, "w")
    _IsWriteF = True  # 标记写入标识                                                                       #标记写入标识
    Tempstr = "Chiptime"
    Tempstr +=  "\tax(g)\tay(g)\taz(g)"
    Tempstr += "\twx(deg/s)\twy(deg/s)\twz(deg/s)"
    Tempstr += "\tAngleX(deg)\tAngleY(deg)\tAngleZ(deg)"
    
    Tempstr += "\tT(°)"
    Tempstr += "\tmagx\tmagy\tmagz"
    Tempstr += "\tlon\tlat"
    Tempstr += "\tYaw\tSpeed"
    Tempstr += "\tq1\tq2\tq3\tq4"
    Tempstr += "\r\n"
    _writeF.write(Tempstr)
    print("开始记录数据")
    time.sleep(1)  # 等待1秒钟进行数据记录
    device.closeDevice()
    endRecord()  # 结束记录数据

def endRecord():
    """
    结束记录数据  End record data
    :return:
    """
    global _writeF
    global _IsWriteF
    _IsWriteF = False             # 标记不可写入标识    Tag cannot write the identity
    _writeF.close()               #关闭文件 Close file
    print("结束记录数据")

if __name__ == '__main__':
    """
    初始化一个设备模型   Initialize a device model
    """
    device = deviceModel.DeviceModel(
        "我的JY901",
        WitProtocolResolver(),
        JY901SDataProcessor(),
        "51_0"
    )



    if (platform.system().lower() == 'linux'):
        device.serialConfig.portName = "/dev/ttyUSB0"   #设置串口   Set serial port
    else:
        device.serialConfig.portName = "COM10"          #设置串口   Set serial port
    device.serialConfig.baud = 9600                     #设置波特率  Set baud rate
    device.openDevice()                                 #打开串口   Open serial port
    readConfig(device)                                  #读取配置信息 Read configuration information
    device.dataProcessor.onVarChanged.append(onUpdate)  #数据更新事件 Data update event
    startRecord()                                       # 开始记录数据    Start recording data
    #chaptime_list,temp_list,accx_list,accy_list,accz_list,anglex_list,angley_list,anglez_list,lon_list,lat_list,yaw_list,speed_list=dataRecord(device)
    print(angley_list)
    input()
    device.closeDevice()
    endRecord()                                         #结束记录数据 End record data
