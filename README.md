# 磁力地图采集系统

## 项目简介
本项目是一个用于采集和处理磁力数据的系统，包含以下主要功能：
- 磁力计数据采集
- 惯性导航系统数据采集
- 数据实时处理与存储
- 图形化用户界面

## 系统组成
- mag_aq.py: 磁力计数据采集模块
- ins_aq.py: 惯性导航系统数据采集模块
- process_mag_data.py: 磁力数据处理模块
- main_gui.py: 主图形界面

## 使用方法
1. 安装依赖：`pip install -r requirements.txt`
2. 运行主程序：`python main_gui.py`
3. 通过图形界面进行数据采集和处理

## 数据存储
- 原始数据存储在mag_data/unprocessed目录
- 处理后的数据存储在mag_data/processed目录
