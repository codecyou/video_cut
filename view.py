# version 1.0.0.3 添加任务，自动完成，单线程
import tkinter as tk
import webbrowser
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox as mBox
import os
import windnd
import threading
import time
from moviepy.editor import VideoFileClip
from tkinter import scrolledtext
import logging

base_dir = os.path.dirname(os.path.abspath(__file__))


# 第一步，创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Log等级总开关

# 第二步，创建一个handler，用于写入日志文件
log_dir = os.path.join(base_dir, 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logfile = os.path.join(log_dir, "log.txt")
fh = logging.FileHandler(logfile, mode='a')  # open的打开模式这里可以进行参考
fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关

# 第三步，再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)   # 输出到console的log等级的开关

# 第四步，定义handler的输出格式
formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 第五步，将logger添加到handler里面
logger.addHandler(fh)
logger.addHandler(ch)


SYSTEM_CODE = "GBK"  # 系统编码格式


def check_path(dir_path, create_flag=False):
    """用于检测输入路径是否正确,
        dir_path        目录路径
        create_flag     标记是否新建目录
                        True如果目录不存在则新建
                        False不新建
    """
    if dir_path:  # 有输入内容
        dir_path = dir_path.strip()  # 防止出现输入' '
        if os.path.exists(dir_path):  # 检查路径是否存在
            # 当输入'/home/'时获取文件名就是''，所以加处理
            dir_path = os.path.abspath(dir_path)
            return dir_path
        else:
            if create_flag:
                # print("输入目录不存在！已为您新建该目录！")
                os.makedirs(dir_path)
                dir_path = os.path.abspath(dir_path)
                return dir_path
            else:
                return
    else:
        print("输入路径有误，请重新输入！")
        return


def get_float_value(key, default_value):
    """用于获取输入框中的值，如果不输入则返回默认值"""
    if key:
        try:
            key = float(key)
        except Exception:
            key = default_value
    else:
        key = default_value
    return key


class Task(object):
    """任务对象类"""
    def __init__(self, pathIn, pathOut, sub_start_time, sub_stop_time, fps, continue_flag=False, original_mtime_flag=False):
        super().__init__()
        self.pathIn = pathIn
        self.pathOut = pathOut
        self.sub_start_time = sub_start_time
        self.sub_stop_time = sub_stop_time
        self.fps = fps
        self.continue_flag = continue_flag
        self.original_mtime_flag = original_mtime_flag
        self.status = 0  # 'status':状态，0：未完成，1：已完成，2：错误


class VideoCutFrame(tk.Frame):  # 继承Frame类
    """视频裁剪"""
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.root = master  # 定义内部变量root
        self.winWidth = 750  # 窗口宽度
        self.winHeight = 600  # 窗口高度
        # 设置窗口大小
        self.set_window()
        self.record_path = None  # 视频导出地址
        self.log_path = logfile  # 日志地址
        self.task_list = []  # 任务列表
        self.task_status_dict = {0: "进行中", 1: "已完成", 2: "错误"}  # 状态码
        self.task_status_color_dict = {0: "blue", 1: "green", 2: "red"}  # 状态码对应颜色
        self.sub_start_time_h = tk.StringVar()  # 获取开始剪切时间 小时
        self.sub_start_time_m = tk.StringVar()  # 获取开始剪切时间 分钟
        self.sub_start_time_s = tk.StringVar()  # 获取开始剪切时间 秒
        self.sub_stop_time_h = tk.StringVar()  # 获取剪切结束时间
        self.sub_stop_time_m = tk.StringVar()  # 获取剪切结束时间
        self.sub_stop_time_s = tk.StringVar()  # 获取剪切结束时间
        self.frameNum = tk.StringVar()  # 视频帧率
        self.invoke_fps_flag = tk.BooleanVar()  # 是否激活帧率输入框
        self.original_mtime_flag = tk.BooleanVar()  # 是否继承原文件修改时间
        self.src_dir = tk.StringVar()
        self.dst_dir = tk.StringVar()
        self.createPage()
        self.run()  # 启动一个子线程用来监听并执行self.task_list 任务列表中的任务

    def set_window(self):
        """设置窗口大小"""
        # 获取屏幕分辨率
        screenWidth = self.root.winfo_screenwidth()
        screenHeight = self.root.winfo_screenheight()
        x = int((screenWidth - self.winWidth) / 2)
        y = int((screenHeight - self.winHeight) / 2)
        # 设置窗口初始位置在屏幕居中
        self.root.geometry("%sx%s+%s+%s" % (self.winWidth, self.winHeight, x, y))

    def dragged_files(self, files):
        """拖拽文件捕获"""
        self.record_path = None
        self.dst_dir.set("")
        for item in files:
            dir_path = item.decode(SYSTEM_CODE)
            self.src_dir.set(dir_path)

    def selectPath(self):
        self.src_dir.set(askopenfilename())
        self.record_path = None
        self.dst_dir.set("")

    def createPage(self):
        """页面布局"""
        self.f_title = ttk.Frame(self)  # 页面标题
        self.f_input = ttk.Frame(self)  # 输入部分
        self.f_state = ttk.Frame(self)  # 进度条
        self.f_content = ttk.Frame(self)  # 显示结果
        self.f_bottom = ttk.Frame(self)  # 页面底部
        self.f_title.pack(fill=tk.BOTH, expand=True)
        self.f_input.pack(fill=tk.BOTH, expand=True)
        self.f_state.pack(fill=tk.BOTH, expand=True)
        self.f_content.pack(fill=tk.BOTH, expand=True)
        self.f_bottom.pack(fill=tk.BOTH, expand=True)

        self.l_title = tk.Label(self.f_title, text='页面', font=('微软雅黑', 12), width=50, height=2)
        self.l_title.pack()
        self.l_title["text"] = "视频裁剪"
        ttk.Label(self.f_input, text='源视频:').grid(row=0, stick=tk.W, pady=10)
        ttk.Entry(self.f_input, textvariable=self.src_dir, width=85).grid(row=0, column=1)
        ttk.Button(self.f_input, text="浏览", command=self.selectPath).grid(row=0, column=2)

        self.f_input_option = ttk.Frame(self.f_input)  # 选项容器
        self.f_input_option.grid(row=2, columnspan=3, stick=tk.EW)
        ttk.Label(self.f_input_option, text='输出格式:').grid(row=0, column=0, stick=tk.W, pady=10)
        ttk.Label(self.f_input_option, text='MP4  ').grid(row=0, column=1, stick=tk.W, pady=10)
        ttk.Checkbutton(self.f_input_option, text="修改帧率", variable=self.invoke_fps_flag, onvalue=True,
                        offvalue=False, command=self.invoke_fps).grid(row=0, column=2, sticky=tk.EW, padx=10)
        self.e_fps = ttk.Entry(self.f_input_option, textvariable=self.frameNum, width=10, state=tk.DISABLED)  # 视频帧率输入框
        self.e_fps.grid(row=0, column=3, stick=tk.W)
        self.frameNum.set("")  # 设置默认值
        ttk.Checkbutton(self.f_input_option, text="继承原修改时间", variable=self.original_mtime_flag, onvalue=True,
                        offvalue=False).grid(row=0, column=4, sticky=tk.EW, padx=10)
        self.original_mtime_flag.set(False)  # 设置默认选中否
        self.f_time_option = ttk.Frame(self.f_input)  # 时间输入容器
        self.f_time_option.grid(row=3, columnspan=3, stick=tk.EW)
        ttk.Label(self.f_time_option, text='开始时间: ').grid(row=1, column=0, stick=tk.W, pady=10)
        ttk.Entry(self.f_time_option, textvariable=self.sub_start_time_h, width=5).grid(row=1, column=1, stick=tk.W)
        ttk.Label(self.f_time_option, text=':').grid(row=1, column=2, stick=tk.W, pady=10)
        ttk.Entry(self.f_time_option, textvariable=self.sub_start_time_m, width=5).grid(row=1, column=3, stick=tk.W)
        ttk.Label(self.f_time_option, text=':').grid(row=1, column=4, stick=tk.W, pady=10)
        ttk.Entry(self.f_time_option, textvariable=self.sub_start_time_s, width=5).grid(row=1, column=5, stick=tk.W)
        ttk.Label(self.f_time_option, text='    结束时间: ').grid(row=1, column=6, stick=tk.W, pady=10)
        ttk.Entry(self.f_time_option, textvariable=self.sub_stop_time_h, width=5).grid(row=1, column=7, stick=tk.W)
        ttk.Label(self.f_time_option, text=':').grid(row=1, column=8, stick=tk.W, pady=10)
        ttk.Entry(self.f_time_option, textvariable=self.sub_stop_time_m, width=5).grid(row=1, column=9, stick=tk.W)
        ttk.Label(self.f_time_option, text=':').grid(row=1, column=10, stick=tk.W, pady=10)
        ttk.Entry(self.f_time_option, textvariable=self.sub_stop_time_s, width=5).grid(row=1, column=11, stick=tk.W)
        ttk.Label(self.f_time_option, text='', width=20).grid(row=1, column=12)  # 占位，无意义
        ttk.Button(self.f_time_option, text="查看日志", command=self.showLog).grid(row=1, column=13)
        ttk.Button(self.f_time_option, text="添加任务", command=self.create_task).grid(row=1, column=14)
        self.l_task_state = ttk.Label(self.f_state, text="当前任务：", font=('微软雅黑', 16))
        self.l_task_state.pack()
        scrolW = 100
        scrolH = 28
        self.scr = scrolledtext.ScrolledText(self.f_content, width=scrolW, height=scrolH, wrap=tk.WORD)
        self.scr.grid(column=0, row=2, columnspan=2, sticky='WE')
        windnd.hook_dropfiles(self.root, func=self.dragged_files)  # 监听文件拖拽操作

    def invoke_fps(self):
        """激活帧率输入框"""
        invoke_fps_flag = self.invoke_fps_flag.get()
        if invoke_fps_flag:
            self.e_fps.config(state=tk.NORMAL)
        else:
            self.frameNum.set('')
            self.e_fps.config(state=tk.DISABLED)

    def showLog(self):
        """查看日志"""
        if self.log_path:
            webbrowser.open(self.log_path)

    def create_task(self):
        """创建任务"""
        pathIn = check_path(self.src_dir.get())
        fps = self.frameNum.get().strip()  # 帧率
        if fps:
            try:
                fps = float(fps)
            except Exception:
                fps = None
        else:
            fps = None

        # 获取截取时间段
        sub_start_time_h = self.sub_start_time_h.get().strip()  # 获取开始剪切时间
        sub_start_time_m = self.sub_start_time_m.get().strip()  # 获取开始剪切时间
        sub_start_time_s = self.sub_start_time_s.get().strip()  # 获取开始剪切时间
        sub_stop_time_h = self.sub_stop_time_h.get().strip()  # 获取剪切的结束时间
        sub_stop_time_m = self.sub_stop_time_m.get().strip()  # 获取剪切的结束时间
        sub_stop_time_s = self.sub_stop_time_s.get().strip()  # 获取剪切的结束时间

        try:
            sub_start_time_h = get_float_value(sub_start_time_h, 0)  # 获取开始剪切时间
            sub_start_time_m = get_float_value(sub_start_time_m, 0)  # 获取开始剪切时间
            sub_start_time_s = get_float_value(sub_start_time_s, 0)  # 获取开始剪切时间
            sub_stop_time_h = get_float_value(sub_stop_time_h, 0)  # 获取剪切的结束时间
            sub_stop_time_m = get_float_value(sub_stop_time_m, 0)  # 获取剪切的结束时间
            sub_stop_time_s = get_float_value(sub_stop_time_s, 0)  # 获取剪切的结束时间
            sub_start_time = sub_start_time_h*3600 + sub_start_time_m*60 + sub_start_time_s
            sub_stop_time = sub_stop_time_h*3600 + sub_stop_time_m*60 + sub_stop_time_s
            file_name = os.path.basename(pathIn)
            self.record_path = os.path.join(os.path.dirname(pathIn), "videoCut")
            pathOut = os.path.join(self.record_path, "%s_(%ss_to_%ss).mp4" % (file_name, sub_start_time, sub_stop_time))
            self.dst_dir.set(pathOut)  # 显示导出路径到界面
            original_mtime_flag = self.original_mtime_flag.get()  # 继承原文件修改时间信息
            if pathIn is None:
                mBox.showerror("路径不存在！", "%s  不存在！请检查！" % self.src_dir.get())
                return
            if pathIn == pathOut:
                mBox.showwarning("警告", "源路径与目标路径一致，有数据混乱风险！请重新规划路径！")
                return
            continue_flag = False

            # 创建任务信息
            task = Task(pathIn, pathOut, sub_start_time, sub_stop_time, fps, continue_flag, original_mtime_flag)
            self.task_list.append(task)
            self.show_tasks()  # 刷新任务列表状态
            mBox.showinfo("ok", "创建任务成功！")
        except Exception as e:
            self.record_path = None
            mBox.showerror("错误！", e)
            return

    def show_tasks(self):
        """用于展示所有任务信息"""
        self.scr.delete(1.0, "end")
        total_count = len(self.task_list)  # 总任务数
        done_count = 0  # 完成任务数
        todo_count = 0  # 等待中的任务数
        error_count = 0  # 错误的任务数
        for task in self.task_list:
            pathIn = task.pathIn
            pathOut = task.pathOut
            sub_start_time = task.sub_start_time
            sub_stop_time = task.sub_stop_time
            fps = task.fps
            continue_flag = task.continue_flag
            original_mtime_flag = task.original_mtime_flag
            status = task.status
            if status == 0:
                todo_count += 1
            elif status == 1:
                done_count += 1
            else:
                error_count += 1
            status = self.task_status_dict.get(status)
            status_color = self.task_status_color_dict.get(task.status)
            if status is None:  # 状态码异常
                status = "状态异常"
                status_color = "orange"
            msg = "PathIn: %s\n" % pathIn
            msg += "PathOut: %s\n" % pathOut
            msg += "截取开始: %s秒\n" % sub_start_time
            msg += "截取结束: %s秒\n" % sub_stop_time
            msg += "帧率: %s\n" % fps
            msg += "还原修改时间: %s\n" % original_mtime_flag
            msg += "状态: "
            self.scr.insert("end", msg)
            self.scr.insert("end", status, status_color)  # 插入任务状态，附带标签
            self.scr.tag_config(status_color, foreground=status_color)
            self.scr.insert("end", "\n\n\n")
        # 更新任务状态标签
        self.l_task_state["text"] = "当前任务：(总共：%s，%s进行中，%s已完成，%s错误)" % (total_count, todo_count, done_count, error_count)

    def do_video_cut_single(self, pathIn, pathOut, sub_start_time, sub_stop_time, fps, continue_flag=False,
                            original_mtime_flag=False):
        """裁剪视频，处理单个文件"""
        start_time = time.time()  # 记录开始时间
        if not os.path.exists(pathIn):
            return
        if pathIn == pathOut:
            print("源路径与目标路径一致！")
            return
        if os.path.isdir(pathOut):
            pathOut = os.path.join(pathOut, os.path.basename(pathIn))
        if continue_flag is True:
            if os.path.exists(pathOut):
                return
        print(pathIn, ">>>", pathOut)
        pathOutDir = os.path.dirname(pathOut)
        if not os.path.exists(pathOutDir):
            os.makedirs(pathOutDir)
        total_sec = VideoFileClip(pathIn).duration
        print("moviepy get totalsec: ", total_sec)
        if sub_stop_time < 0:  # 截取倒数第几秒
            sub_stop_time = total_sec + sub_stop_time
        video = VideoFileClip(pathIn)  # 视频文件加载
        video = video.subclip(sub_start_time, sub_stop_time)  # 执行剪切操作

        # video.write_videofile(pathOut, fps=fps, remove_temp=True)  # 输出文件
        video.write_videofile(pathOut, fps=fps, audio_codec='aac', remove_temp=True)  # 输出文件

        # 将裁剪后视频修改时间变更为源视频修改时间
        if original_mtime_flag is True:
            timestamp = os.path.getmtime(pathIn)
            os.utime(pathOut, (timestamp, timestamp))
        msg = "裁剪%s 第%s秒至第%s秒视频完成!" % (pathIn, sub_start_time, sub_stop_time)
        print(msg)
        msg += "总用时%.3fs" % (time.time() - start_time)
        logger.info(msg)
        # mBox.showinfo('完成！', msg)

    def run_task(self):
        """循环检测并执行任务列表里的任务"""
        while True:
            if len(self.task_list):
                for task in self.task_list:
                    if not (task.status == 0):
                        continue
                    pathIn = task.pathIn
                    pathOut = task.pathOut
                    sub_start_time = task.sub_start_time
                    sub_stop_time = task.sub_stop_time
                    fps = task.fps
                    continue_flag = task.continue_flag
                    original_mtime_flag = task.original_mtime_flag
                    args = (pathIn, pathOut, sub_start_time, sub_stop_time, fps, continue_flag, original_mtime_flag)
                    try:
                        self.do_video_cut_single(*args)  # 自动拆包传参
                        task.status = 1
                        print("task:%s complete!" % str(task))
                    except Exception as e:
                        task.status = 2
                        print("出错了：", e)
                        msg = "裁剪%s 第%s秒至第%s秒视频出错!" % (pathIn, sub_start_time, sub_stop_time)
                        msg += " 错误：%s" % e
                        logger.error(msg)
                    finally:
                        self.show_tasks()  # 刷新任务列表状态
            time.sleep(1)

    def run(self):
        """运行程序"""
        t = threading.Thread(target=self.run_task)
        t.setDaemon(True)
        t.start()





