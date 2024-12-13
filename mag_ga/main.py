import subprocess

def run_programs_for_duration(duration):
    # 要运行的两个程序的命令，传递duration作为参数
    program1 = ["python", "mag_ga\\ins_aq.py", str(duration)]  # 将duration作为字符串传递
    program2 = ["python", "mag_ga\\mag_aq.py", str(duration)]  # 将duration作为字符串传递

    # 启动并行运行程序
    process1 = subprocess.Popen(program1)
    process2 = subprocess.Popen(program2)

    # 等待两个程序完成
    process1.wait()
    process2.wait()

    print(f"两个程序都已完成，程序运行时间为 {duration} 秒。")

if __name__ == "__main__":
    try:
        duration = int(input("请输入程序运行的时间（秒）："))
        run_programs_for_duration(duration)
    except ValueError:
        print("请输入一个有效的数字。")
