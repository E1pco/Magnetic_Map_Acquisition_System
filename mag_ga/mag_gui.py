import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog,
                           QComboBox, QMessageBox, QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import threading
import subprocess
import manual_control

class DataCollectionThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, duration, save_path):
        super().__init__()
        self.duration = duration
        self.save_path = save_path
        self.is_running = True
        self.mag_process = None
        self.ins_process = None
        
    def run(self):
        try:
            # 获取当前脚本目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 为INS数据创建时间戳文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ins_filename = f"ins_data_{timestamp}.csv"
            
            # 构建命令参数
            mag_cmd = ["python3", os.path.join(script_dir, "mag_aq.py"), 
                      str(self.duration)]
            
            # INS使用默认串口
            ins_cmd = ["python3", os.path.join(script_dir, "ins_aq.py"),
                      str(self.duration)]
            
            # 使用subprocess运行两个脚本，并捕获输出
            self.progress_signal.emit("正在启动数据采集...")
            
            self.mag_process = subprocess.Popen(mag_cmd, 
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True)
            
            self.ins_process = subprocess.Popen(ins_cmd,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            text=True)
            
            self.progress_signal.emit("数据采集已启动")
            
            # 等待完成或手动停止
            while self.is_running:
                # 检查进程状态
                mag_status = self.mag_process.poll()
                ins_status = self.ins_process.poll()
                
                # 如果有错误输出，发送到进度信号
                self.check_process_output(self.mag_process, "mag")
                self.check_process_output(self.ins_process, "INS")
                
                # 如果两个进程都结束了
                if mag_status is not None and ins_status is not None:
                    if mag_status == 0 and ins_status == 0:
                        self.progress_signal.emit("数据采集完成")
                        self.finished_signal.emit(True)
                    else:
                        self.progress_signal.emit("数据采集异常结束")
                        self.finished_signal.emit(False)
                    break
                
                self.msleep(100)  # 每100ms检查一次状态
            
            # 如果是手动停止，给进程发送终止信号
            if self.is_running:
                self.stop()
            
        except Exception as e:
            self.progress_signal.emit(f"错误: {str(e)}")
            self.finished_signal.emit(False)
    
    def stop(self):
        self.is_running = False
        # 终止进程
        if self.mag_process and self.mag_process.poll() is None:
            self.mag_process.terminate()
            self.mag_process.wait()
        if self.ins_process and self.ins_process.poll() is None:
            self.ins_process.terminate()
            self.ins_process.wait()
    
    def check_process_output(self, process, name):
        if process and process.poll() is None:
            # 检查错误输出
            if process.stderr:
                err = process.stderr.readline()
                if err:
                    self.progress_signal.emit(f"{name}错误: {err.strip()}")
            # 检查标准输出
            if process.stdout:
                out = process.stdout.readline()
                if out:
                    self.progress_signal.emit(f"{name}: {out.strip()}")
    
class PlotUpdateThread(QThread):
    update_signal = pyqtSignal(pd.DataFrame)
    error_signal = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        try:
            df = pd.read_csv(self.file_path)
            self.update_signal.emit(df)
        except Exception as e:
            self.error_signal.emit(str(e))

class DataViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.plot_thread = None
        
    def update_plot(self, df):
        try:
            # 更新数据图
            self.ax1.clear()
            self.ax1.plot(df['Time'], df['Magnitude'], label='Raw Data')
            self.ax1.plot(df['Time'], df['Filtered Magnitude'], label='Filtered Data')
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Magnetic Field Strength')
            self.ax1.grid(True)
            self.ax1.legend()

            # 更新地图
            self.ax2.clear()
            if 'Latitude' in df.columns and 'Longitude' in df.columns:
                self.ax2.scatter(df['Longitude'], df['Latitude'], c=df['Magnitude'], 
                               cmap='viridis', s=50)
                self.ax2.set_xlabel('Longitude')
                self.ax2.set_ylabel('Latitude')
                self.ax2.grid(True)
            else:
                self.ax2.text(0.5, 0.5, 'No Location Data', 
                            ha='center', va='center')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            # 计算并更新统计信息
            if len(df) > 0:
                sample_count = len(df)
                max_value = df['Magnitude'].max()
                min_value = df['Magnitude'].min()
                avg_value = df['Magnitude'].mean()
                
                # 更新统计信息显示
                self.parent().sample_count_label.setText(f"Sample Count: {sample_count}")
                self.parent().max_value_label.setText(f"Max Value: {max_value:.2f}")
                self.parent().min_value_label.setText(f"Min Value: {min_value:.2f}")
                self.parent().avg_value_label.setText(f"Average Value: {avg_value:.2f}")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"绘图失败: {str(e)}")
        
    def plot_data(self, file_path):
        if self.plot_thread is not None and self.plot_thread.isRunning():
            self.plot_thread.wait()
            
        self.plot_thread = PlotUpdateThread(file_path)
        self.plot_thread.update_signal.connect(self.update_plot)
        self.plot_thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "错误", f"加载数据失败: {msg}"))
        self.plot_thread.start()

class MainWindow(QMainWindow):
    progress_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetometer Data Acquisition System")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主widget和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # 左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        control_panel.setFixedWidth(350)
        control_panel.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QLabel {
                font-weight: bold;
                color: #333;
                min-width: 80px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                min-width: 80px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                min-width: 150px;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        
        # 采集参数配置
        config_group = QGroupBox("采集参数")
        config_layout = QVBoxLayout()
        config_group.setLayout(config_layout)
        
        # 采集时间
        duration_layout = QHBoxLayout()
        duration_label = QLabel("采集时间(秒):")
        self.duration_edit = QLineEdit("10")
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_edit)
        
        # 数据保存路径
        save_path_layout = QHBoxLayout()
        save_path_label = QLabel("保存路径:")
        self.save_path_edit = QLineEdit("mag_data")
        self.save_path_button = QPushButton("浏览")
        self.save_path_button.clicked.connect(self.select_save_path)
        save_path_layout.addWidget(save_path_label)
        save_path_layout.addWidget(self.save_path_edit)
        save_path_layout.addWidget(self.save_path_button)
        
        # 添加到配置面板
        config_layout.addLayout(duration_layout)
        config_layout.addLayout(save_path_layout)
        
        # 手动启停区域
        manual_control_group = QGroupBox("手动启停")
        manual_control_layout = QVBoxLayout()
        manual_control_group.setLayout(manual_control_layout)
        
        self.start_manual_button = QPushButton("开始手动采集")
        self.start_manual_button.clicked.connect(self.start_manual_collection)
        manual_control_layout.addWidget(self.start_manual_button)
        
        self.stop_manual_button = QPushButton("停止手动采集")
        self.stop_manual_button.clicked.connect(self.stop_manual_collection)
        manual_control_layout.addWidget(self.stop_manual_button)
        
        # 控制按钮
        self.start_button = QPushButton("开始采集")
        self.start_button.clicked.connect(self.start_collection)
        self.stop_button = QPushButton("停止采集")
        self.stop_button.clicked.connect(self.stop_collection)
        self.stop_button.setEnabled(False)
        
        # 数据文件操作
        file_layout = QHBoxLayout()
        self.file_button = QPushButton("选择数据文件")
        self.file_button.clicked.connect(self.select_file)
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setEnabled(False)
        file_layout.addWidget(self.file_button)
        file_layout.addWidget(self.export_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        
        # 右侧数据显示
        self.data_viewer = DataViewerWidget()
        
        # 初始化统计信息显示
        # self.data_viewer.parent = lambda: self
        
        # 添加所有控件到主布局
        control_layout.addWidget(config_group)
        control_layout.addSpacing(10)
        control_layout.addWidget(manual_control_group)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.start_button)
        control_layout.addSpacing(5)
        control_layout.addWidget(self.stop_button)
        control_layout.addSpacing(10)
        control_layout.addLayout(file_layout)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.progress_bar)
        control_layout.addStretch()
        
        # 添加控制面板和数据显示到主布局
        layout.addWidget(control_panel)
        layout.addWidget(self.data_viewer)
        
        # 初始化
        self.collection_thread = None
        self.manual_control = manual_control.ManualControl(self.collection_thread)
        
    def select_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径", "mag_data")
        if path:
            self.save_path_edit.setText(path)

    def start_collection(self):
        try:
            duration = int(self.duration_edit.text())
            if duration < 0:
                raise ValueError("采集时间必须大于或等于0")
            elif duration == 0:
                self.collection_thread.stop()  # 手动结束采样
                self.progress_signal.emit("手动结束采样")
                if self.collection_thread.mag_process:
                    self.collection_thread.mag_process.stdin.write(b'\n')
                    self.collection_thread.mag_process.stdin.flush()
                if self.collection_thread.ins_process:
                    self.collection_thread.ins_process.stdin.write(b'\n')
                    self.collection_thread.ins_process.stdin.flush()
                self.start_button.setEnabled(True)  # 重新启用开始按钮
                self.stop_button.setEnabled(False)  # 禁用停止按钮
                return
                
            save_path = self.save_path_edit.text()
            
            # 创建保存目录
            os.makedirs(save_path, exist_ok=True)
            
            self.collection_thread = DataCollectionThread(duration, save_path)
            self.collection_thread.progress_signal.connect(self.update_progress)
            self.collection_thread.finished_signal.connect(self.collection_finished)
            self.collection_thread.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setRange(0, 0)  # 显示忙碌状态
            
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            
    def stop_collection(self):
        if self.collection_thread and self.collection_thread.isRunning():
            self.collection_thread.stop()  # 使用新的stop方法
            self.collection_thread.wait()  # 等待线程结束
            self.collection_finished(True)  # 标记为正常完成
            
    def collection_finished(self, success):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        if success:
            QMessageBox.information(self, "完成", "数据采集完成")
            # 自动加载最新的数据文件
            data_dir = "mag_data"
            if os.path.exists(data_dir):
                files = [f for f in os.listdir(data_dir) if f.endswith('_processed.csv')]
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
                    self.data_viewer.plot_data(os.path.join(data_dir, latest_file))
                    
    def update_progress(self, message):
        QMessageBox.warning(self, "错误", message)
        
    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "mag_data",
            "CSV files (*.csv)"
        )
        if file_name:
            self.data_viewer.plot_data(file_name)
            self.export_button.setEnabled(True)
            self.current_file = file_name

    def export_data(self):
        if not hasattr(self, 'current_file'):
            return
            
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "导出数据文件",
            "",
            "CSV Files (*.csv);;All Files (*)",
            options=options
        )
        
        if file_name:
            try:
                # 确保文件扩展名
                if not file_name.endswith('.csv'):
                    file_name += '.csv'
                    
                # 读取并保存数据
                df = pd.read_csv(self.current_file)
                df.to_csv(file_name, index=False)
                QMessageBox.information(self, "成功", f"数据已成功导出到 {file_name}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")

    def start_manual_collection(self):
        duration = 0  # 手动采集时设置为0
        self.manual_control.start_collection(duration)
        self.start_button.setEnabled(False)  # 禁用开始按钮
        self.stop_button.setEnabled(True)  # 启用停止按钮

    def stop_manual_collection(self):
        self.manual_control.stop_collection()  # 停止手动采集
        self.start_button.setEnabled(True)  # 重新启用开始按钮
        self.stop_button.setEnabled(False)  # 禁用停止按钮

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
