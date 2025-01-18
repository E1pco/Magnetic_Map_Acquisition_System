class ManualControl:
    def __init__(self, collection_thread):
        self.collection_thread = collection_thread

    def start_collection(self, duration):
        if duration < 0:
            raise ValueError("采集时间必须大于或等于0")
        elif duration == 0:
            self.stop_collection()  # 手动结束采样
            return
        # 启动采集逻辑
        # 这里可以添加启动采集的代码

    def stop_collection(self):
        if self.collection_thread is not None:
            self.collection_thread.stop()  # 手动结束采样
            if self.collection_thread.mag_process:
                self.collection_thread.mag_process.stdin.write(b'\n')
                self.collection_thread.mag_process.stdin.flush()
            if self.collection_thread.ins_process:
                self.collection_thread.ins_process.stdin.write(b'\n')
                self.collection_thread.ins_process.stdin.flush()
        else:
            print("没有正在进行的采样线程")
