import subprocess
import threading
import sys
import os

def run_programs_for_duration(duration):
    # 要运行的两个程序的命令，传递duration作为参数
    program1 = ["python3", "/home/elpco/Python_Project/Magnetic_Map_Acquisition_System/mag_ga/ins_aq.py", str(duration)]
    program2 = ["python3", "/home/elpco/Python_Project/Magnetic_Map_Acquisition_System/mag_ga/mag_aq.py", str(duration)]

    # 创建管道用于进程通信，只将标准错误重定向到/dev/null
    with open(os.devnull, 'w') as devnull:
        process1 = subprocess.Popen(program1, 
                                  stdin=subprocess.PIPE, 
                                  stderr=devnull)
        process2 = subprocess.Popen(program2, 
                                  stdin=subprocess.PIPE, 
                                  stderr=devnull)

        if duration == 0:
            # 等待用户按回车
            print("按回车键停止数据采集...")
            input()
            # 向两个进程发送回车
            try:
                if process1.poll() is None:  # 如果进程还在运行
                    process1.stdin.write(b'\n')
                    process1.stdin.flush()
            except:
                pass
            try:
                if process2.poll() is None:  # 如果进程还在运行
                    process2.stdin.write(b'\n')
                    process2.stdin.flush()
            except:
                pass

        # 等待两个程序完成
        process1.wait()
        process2.wait()

        if duration > 0:
            print(f"两个程序都已完成，程序运行时间为 {duration} 秒。")
        else:
            print("数据采集已结束。")

if __name__ == "__main__":
    try:
        duration = input("请输入程序运行的时间（秒，输入0表示手动停止）：")
        duration = int(duration)
        if duration < 0:
            print("时间不能为负数")
            sys.exit(1)
        run_programs_for_duration(duration)
    except ValueError:
        print("请输入一个有效的数字。")
        sys.exit(1)
#