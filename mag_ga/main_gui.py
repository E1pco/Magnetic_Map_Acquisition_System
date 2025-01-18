import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QLineEdit, QMessageBox, 
                            QProgressBar, QFrame)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer
import subprocess
import os
from datetime import datetime

class DataAcquisitionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.process1 = None
        self.process2 = None
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.elapsed_time = 0

    def initUI(self):
        self.setWindowTitle('数据采集系统')
        self.setFixedSize(400, 300)
        
        # 设置主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(20)

        # 设置标题样式
        title = QLabel('数据采集系统')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 输入区域
        input_layout = QVBoxLayout()
        input_layout.setSpacing(0)
        
        # 运行时间输入
        self.duration_label = QLabel('运行时间（秒，0表示手动停止）：')
        self.duration_label.setFont(QFont('Arial', 8))
        input_layout.addWidget(self.duration_label)

        self.duration_input = QLineEdit()
        self.duration_input.setText('0')
        self.duration_input.setFont(QFont('Arial', 10))
        self.duration_input.setMinimumWidth(35)  # 设置合适的宽度
        self.duration_input.setStyleSheet("""
            padding: 12px;
            font-size: 14px;
            border: 2px solid #05B8CC;
            border-radius: 6px;
        """)
        input_layout.addWidget(self.duration_input)

        main_layout.addLayout(input_layout)

        # 状态显示
        self.status_label = QLabel('状态：等待开始')
        self.status_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 10px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # 开始按钮
        self.start_button = QPushButton(' 开始采集')
        self.start_button.setIcon(QIcon.fromTheme('media-playback-start'))
        self.start_button.setFont(QFont('Arial', 7))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_acquisition)
        button_layout.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton(' 停止采集')
        self.stop_button.setIcon(QIcon.fromTheme('media-playback-stop'))
        self.stop_button.setFont(QFont('Arial', 7))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_acquisition)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def update_progress(self):
        if self.elapsed_time < self.total_duration:
            self.elapsed_time += 1
            progress = int((self.elapsed_time / self.total_duration) * 100)
            self.progress_bar.setValue(progress)
        else:
            self.timer.stop()

    def start_acquisition(self):
        try:
            duration = int(self.duration_input.text())
            if duration < 0:
                QMessageBox.warning(self, '错误', '时间不能为负数')
                return

            self.start_time = datetime.now()
            self.status_label.setText(f'状态：运行中（时间：{duration}秒）')
            
            # 禁用开始按钮，启用停止按钮
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.duration_input.setEnabled(False)

            self.run_programs(duration)

        except ValueError:
            QMessageBox.warning(self, '错误', '请输入有效的数字')

    def stop_acquisition(self):
        if self.process1 or self.process2:
            # 先发送停止信号
            self.send_stop_signal()
            
            # 等待进程结束
            if self.process1:
                try:
                    self.process1.wait(timeout=300)
                except subprocess.TimeoutExpired:
                    pass
            if self.process2:
                try:
                    self.process2.wait(timeout=300)
                except subprocess.TimeoutExpired:
                    pass
            
            # 强制终止进程
            self.cleanup_processes()
            
            # 更新状态
            self.status_label.setText('状态：已停止')
            
            # 检查是否有来自ins_aq的最终消息
            try:
                with open("/dev/shm/ins_final_msg", "r") as f:
                    final_msg = f.read()
                    os.remove("/dev/shm/ins_final_msg")
            except FileNotFoundError:
                final_msg = '数据采集已停止'
                
            QMessageBox.information(self, '信息', final_msg)
        
        # 重置UI状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.duration_input.setEnabled(True)

    def run_programs(self, duration):
        program1 = ["python3", "mag_ga/ins_aq.py", str(duration)]
        program2 = ["python3", "mag_ga/mag_aq.py", str(duration)]

        with open(os.devnull, 'w') as devnull:
            self.process1 = subprocess.Popen(program1, 
                                           stdin=subprocess.PIPE, 
                                           stderr=devnull)
            self.process2 = subprocess.Popen(program2, 
                                           stdin=subprocess.PIPE, 
                                           stderr=devnull)

        if duration == 0:
            return  # 等待手动停止

        # 如果设置了时间，等待程序完成
        self.process1.wait()
        self.process2.wait()
        self.cleanup_processes()
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.status_label.setText('状态：已完成')
        
        # 检查是否有来自ins_aq的最终消息
        try:
            with open("/dev/shm/ins_final_msg", "r") as f:
                final_msg = f.read()
                os.remove("/dev/shm/ins_final_msg")
        except FileNotFoundError:
            final_msg = f'数据采集完成\n运行时间：{elapsed_time:.1f}秒'
            
        QMessageBox.information(self, '完成', final_msg)

    def send_stop_signal(self):
        try:
            if self.process1 and self.process1.poll() is None:
                self.process1.stdin.write(b'\n')
                self.process1.stdin.flush()
        except:
            pass

        try:
            if self.process2 and self.process2.poll() is None:
                self.process2.stdin.write(b'\n')
                self.process2.stdin.flush()
        except:
            pass

    def cleanup_processes(self):
        if self.process1:
            try:
                self.process1.terminate()
                self.process1.wait(timeout=10)
                if self.process1.poll() is None:
                    self.process1.kill()
            except:
                pass
            finally:
                self.process1 = None
                
        if self.process2:
            try:
                self.process2.terminate()
                self.process2.wait(timeout=10)
                if self.process2.poll() is None:
                    self.process2.kill()
            except:
                pass
            finally:
                self.process2 = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataAcquisitionApp()
    window.show()
    sys.exit(app.exec_())
