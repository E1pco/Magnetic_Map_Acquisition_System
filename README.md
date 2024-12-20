# Magnetic_Map_Acquisition_System
# 磁场数据采集系统

## 简介
本项目是一个磁场数据采集系统，旨在从传感器中获取磁场数据并进行处理。系统由多个脚本组成，能够并行运行，实时采集和记录数据。

## 目录结构
magnetic-map-acquisition-system/  │ ├── mag_ga/  
              │ ├── mag_aq.py # 磁场数据采集脚本  
              │ └── ins_aq.py # 传感器数据处理脚本   
              │ └── main.py # 主程序，负责并行运行脚本  
              │ └──ins_data # 存放imu和gps传感器数据的文件夹  
              │ └──mag_data # 存放磁场传感器数据的文件夹


## 安装依赖
在使用之前，请确保安装以下Python库：  
```
pip install pyserial
pip install numpy
pip install matplotlib
```



## 启动项目
在终端中运行主程序：  

```
python main.py
```

该程序将并行运行 mag_aq.py 和 ins_aq.py 两个脚本，用于采集和处理磁场数据。运行完成后，会输出当前的时间戳。  
并绘制数据图


## 使用说明
mag_aq.py：负责从磁场传感器读取数据并进行处理。  
ins_aq.py：与 传感器进行通信，获取相关姿态数据。  

## 注意事项
确保传感器设备正确连接并配置好串口。  
根据实际需要调整串口设置和脚本参数。  
项目已经在Ubuntu 22.04和Windows 11上测试通过。
