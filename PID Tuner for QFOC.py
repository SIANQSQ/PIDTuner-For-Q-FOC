
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import time
import serial
import serial.tools.list_ports
import socket
import time
VERSION = "1.0.0"

class EnhancedPIDControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PID 调参系统")
        self.root.geometry("1200x700")  # 设置窗口大小
        self.root.iconbitmap('icon.ico')   # 更改窗口图标
        # 通信设置变量
        self.ip_address = tk.StringVar(value="172.20.10.2")
        self.port = tk.StringVar(value="80")
        self.serial_port = tk.StringVar(value="COM1")
        self.baudrate = tk.IntVar(value=9600)
        self.communication_mode = tk.StringVar(value="http")  # http 或 serial
        self.isConnected = False   #是否连接成功
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建通信设置区域
        self.create_communication_settings(main_frame)
        
        # 创建三路PID控制区域
        self.create_pid_controls(main_frame)
        
        # 创建反馈显示区域
        self.create_feedback_display(main_frame)
        
        # 创建操作按钮
        self.create_action_buttons(main_frame)
        
        # 初始化串口
        self.ser = None
        self.serial_thread = None
        self.serial_running = False

    def check_connection_func(self):
        """检查IP连接状态"""
        try:
            # 创建socket连接测试
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 设置超时时间
            result = sock.connect_ex((self.ip_address.get(), int(self.port.get())))
            sock.close()
            if(result != 0):
                self.NetworkInL.create_oval(2, 2, 10, 10, fill='red', outline='')
                self.NetworkLab.config(text="连接异常")
            else:
                self.NetworkInL.create_oval(2, 2, 10, 10, fill='green', outline='')
                self.NetworkLab.config(text="已连接")
            
            
        except:
                self.NetworkInL.create_oval(2, 2, 10, 10, fill='red', outline='')
                
    def check_connection(self):
        while(1):
            self.check_connection_func()
            time.sleep(5)            
        
    def create_communication_settings(self, parent):
        """创建通信设置区域"""
        comm_frame = ttk.LabelFrame(parent, text="通信设置", padding="10")
        comm_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 通信方式选择
        ttk.Label(comm_frame, text="通信方式:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Combobox(comm_frame, textvariable=self.communication_mode, 
                    values=["http", "serial"], state="readonly", width=10).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # HTTP设置
        http_frame = ttk.Frame(comm_frame)
        http_frame.grid(row=0, column=2, columnspan=40, sticky=tk.W)
        
        ttk.Label(http_frame, text="IP地址:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(http_frame, textvariable=self.ip_address, width=15).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(http_frame, text="端口:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(http_frame, textvariable=self.port, width=8).pack(side=tk.LEFT, padx=(0, 5))


        self.NetworkInL = tk.Canvas(http_frame, width=12, height=12, highlightthickness=0)
        self.NetworkInL.pack(side=tk.LEFT)
        self.NetworkInL.create_oval(2, 2, 10, 10, fill='red', outline='')
        self.NetworkLab = ttk.Label(http_frame, text="连接异常")
        self.NetworkLab.pack(side=tk.LEFT, padx=(5, 15))
        # 串口设置
        serial_frame = ttk.Frame(comm_frame)
        serial_frame.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(serial_frame, text="串口:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 获取可用串口
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.serial_combobox = ttk.Combobox(serial_frame, textvariable=self.serial_port, 
                                           values=ports, state="readonly", width=10)
        self.serial_combobox.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(serial_frame, text="波特率:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Combobox(serial_frame, textvariable=self.baudrate, 
                    values=[9600, 19200, 38400, 57600, 115200], state="readonly", width=10).pack(side=tk.LEFT)
        
        # 刷新串口按钮
        ttk.Button(serial_frame, text="刷新串口", command=self.refresh_serial_ports).pack(side=tk.LEFT, padx=(20, 0))
        
        # 连接/断开串口按钮
        self.serial_connect_btn = ttk.Button(serial_frame, text="连接串口", command=self.toggle_serial_connection)
        self.serial_connect_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 绑定通信方式变化事件
        self.communication_mode.trace_add('write', self.on_communication_mode_changed)
        self.ip_address.trace_add('write',self.on_ip_address_changed)
        self.port.trace_add('write',self.on_port_changed)
        self.on_communication_mode_changed()  # 初始化显示状态

        self.check_connection_thread = threading.Thread(target=self.check_connection, daemon=True)
        self.check_connection_thread.start() #检测连接情况

    def on_communication_mode_changed(self, *args):
        """通信方式改变时的回调"""
        try:
            self.append_feedback(f"通讯模式已经切换为 {self.communication_mode.get()}")
        except:
            pass
    
    def on_ip_address_changed(self, *args):
        """通信IP改变时的回调"""
        try:
            self.append_feedback(f"连接IP: {self.ip_address.get()}")
            #self.check_connection_func()
        except:
            pass

    def on_port_changed(self, *args):
        """通信方式改变时的回调"""
        try:
            self.append_feedback(f"连接端口: {self.port.get()}")
        except:
            pass
        
            
    def refresh_serial_ports(self):
        """刷新可用串口列表"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.serial_combobox['values'] = ports
        if ports and self.serial_port.get() not in ports:
            self.serial_port.set(ports[0])
            
    def toggle_serial_connection(self):
        """连接或断开串口"""
        if self.ser is None or not self.serial_running:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        """连接串口"""
        try:
            self.ser = serial.Serial(
                port=self.serial_port.get(),
                baudrate=self.baudrate.get(),
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
            self.serial_running = True
            self.serial_connect_btn.config(text="断开串口")
            self.append_feedback(f"已连接到串口 {self.serial_port.get()}")
            
            # 启动串口读取线程
            self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.serial_thread.start()
            
        except serial.SerialException as e:
            messagebox.showerror("错误", f"无法打开串口: {str(e)}")
            
    def disconnect_serial(self):
        """断开串口连接"""
        if self.ser:
            self.serial_running = False
            self.ser.close()
            self.ser = None
            self.serial_connect_btn.config(text="连接串口")
            self.append_feedback("已断开串口连接")
            
    def read_serial(self):
        """从串口读取数据"""
        while self.serial_running and self.ser:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        self.append_feedback(f"接收: {data}")
            except:
                break
                
    def create_pid_controls(self, parent):
        """创建三路PID控制区域"""
        pid_frame = ttk.LabelFrame(parent, text="PID 参数设置", padding="10")
        pid_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建三列框架用于放置三路PID
        self.pid_columns = []
        for i in range(6):
            col_frame = ttk.Frame(pid_frame)
            col_frame.grid(row=0, column=i, padx=10, sticky=tk.N)
            self.pid_columns.append(col_frame)
            
            # 为每路PID创建标题
            ttk.Label(col_frame, text=f"PID {i+1}", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
            
            # 为每路PID创建控制组件
            self.create_single_pid_controls(col_frame, i+1)
            
    def create_single_pid_controls(self, parent, pid_num):
        """创建单路PID控制组件"""
        # 存储PID参数的变量
        kp_var = tk.DoubleVar(value=1.0)
        ki_var = tk.DoubleVar(value=0.1)
        kd_var = tk.DoubleVar(value=0.05)
        limit_var = tk.DoubleVar(value=10.0)
        
        # Kp 控制
        ttk.Label(parent, text="比例系数 (Kp):").pack(anchor=tk.W, pady=(5, 0))
        self.create_slider_and_entry(parent, kp_var, 0.0, 100.0)
        
        # Ki 控制
        ttk.Label(parent, text="积分系数 (Ki):").pack(anchor=tk.W, pady=(10, 0))
        self.create_slider_and_entry(parent, ki_var, 0.0, 5.0)
        
        # Kd 控制
        ttk.Label(parent, text="微分系数 (Kd):").pack(anchor=tk.W, pady=(10, 0))
        self.create_slider_and_entry(parent, kd_var, 0.0, 5.0)
        
        # 限幅设置
        ttk.Label(parent, text="输出限幅:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(15, 5))
        
        limit_frame = ttk.Frame(parent)
        limit_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(limit_frame, text="限幅:").pack(side=tk.LEFT)
        min_entry = ttk.Entry(limit_frame, width=8, textvariable=limit_var)
        min_entry.pack(side=tk.LEFT, padx=(5, 15))
        
        
        # 存储变量以便后续访问
        setattr(self, f"pid{pid_num}_kp", kp_var)
        setattr(self, f"pid{pid_num}_ki", ki_var)
        setattr(self, f"pid{pid_num}_kd", kd_var)
        setattr(self, f"pid{pid_num}_min", limit_var)
        
    def create_slider_and_entry(self, parent, variable, min_val, max_val):
        """创建滑块和输入框组合"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(5, 0))
        
        # 输入框
        entry = ttk.Entry(frame, width=8, textvariable=variable)
        entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 滑块
        slider = ttk.Scale(frame, from_=min_val, to=max_val, 
                          orient=tk.HORIZONTAL, variable=variable)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 绑定事件
        entry.bind('<Return>', lambda e: self.validate_entry(variable, min_val, max_val))
        variable.trace_add('write', lambda *args: self.validate_slider(variable, slider, min_val, max_val))
        
        return entry, slider
    
    def validate_entry(self, var, min_val, max_val):
        """验证输入框的值是否在有效范围内"""
        try:
            value = float(var.get())
            if value < min_val:
                var.set(min_val)
            elif value > max_val:
                var.set(max_val)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            var.set(min_val)  # 重置为最小值
    
    def validate_slider(self, var, slider, min_val, max_val):
        """确保滑块值在有效范围内"""
        value = var.get()
        if value < min_val:
            var.set(min_val)
        elif value > max_val:
            var.set(max_val)
        else:
            # 只有当值在范围内时才更新滑块
            if abs(slider.get() - value) > 0.001:
                slider.set(value)
                
    def create_feedback_display(self, parent):
        """创建反馈显示区域"""
        feedback_frame = ttk.LabelFrame(parent, text="消息日志", padding="10")
        feedback_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建带滚动条的文本框
        self.feedback_text = scrolledtext.ScrolledText(feedback_frame, wrap=tk.WORD, height=10)
        self.feedback_text.pack(fill=tk.BOTH, expand=True)
        self.feedback_text.config(state=tk.DISABLED)  # 设置为只读
        
    def append_feedback(self, message):
        """向反馈文本框添加消息"""
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.feedback_text.see(tk.END)  # 自动滚动到底部
        self.feedback_text.config(state=tk.DISABLED)
    
    def info(self):
        self.append_feedback("PID调参上位机 "+VERSION)
        self.append_feedback("作者:屈圣桥")
        self.append_feedback("更多信息请访问: qsq.cool")

    def create_action_buttons(self, parent):
        """创建操作按钮"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 发送所有按钮
        ttk.Button(button_frame, text="发送所有PID参数", command=self.send_all_parameters).pack(side=tk.LEFT, padx=(0, 10))
        
        # 发送单路按钮
        for i in range(6):
            ttk.Button(button_frame, text=f"发送PID{i+1}参数", 
                      command=lambda idx=i+1: self.send_single_parameters(idx)).pack(side=tk.LEFT, padx=(0, 10))
        
        # 重置按钮
        ttk.Button(button_frame, text="重置所有参数", command=self.reset_all_parameters).pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空反馈按钮
        ttk.Button(button_frame, text="清空反馈", command=self.clear_feedback).pack(side=tk.LEFT)

        ttk.Button(button_frame, text="了解更多", command=self.info).pack(side=tk.RIGHT)
        
    def send_all_parameters(self):
        """发送所有PID参数"""
        all_params = []
        
        for i in range(1, 4):
            params = {
                "channel": i,
                "p": getattr(self, f"pid{i}_kp").get(),
                "i": getattr(self, f"pid{i}_ki").get(),
                "d": getattr(self, f"pid{i}_kd").get(),
                "limit": getattr(self, f"pid{i}_min").get()
            }
            self.send_single_parameters(params, f"PID{i}参数")
        
    def send_single_parameters(self, pid_num):
        """发送单路PID参数"""
        params = [{
            "channel": pid_num,
            "p": getattr(self, f"pid{pid_num}_kp").get(),
            "i": getattr(self, f"pid{pid_num}_ki").get(),
            "d": getattr(self, f"pid{pid_num}_kd").get(),
            "limit": getattr(self, f"pid{pid_num}_min").get()
        }]
        
        self.send_data(params, f"PID{pid_num}参数")
        
    def send_data(self, data, description):
        """发送数据（HTTP或串口）"""
        if self.communication_mode.get() == "http":
            self.send_http_request(data, description)
        else:
            self.send_serial_data(data, description)
            
    def send_http_request(self, data, description):
        """发送HTTP请求"""
        try:
            url = f"http://{self.ip_address.get()}:{self.port.get()}/setpid"
            self.append_feedback(f"发送HTTP请求到 {url}")
            
            response = requests.get(
                f"http://{self.ip_address.get()}:{self.port.get()}/setpid", 
                params=data[0],
                timeout=2
            )
            print(data)
           # self.append_feedback(text=f"模式设置成功: {response.text}")

            # 在实际应用中，这里应该发送实际的HTTP请求
            # 以下代码模拟发送过程
            #self.append_feedback(f"发送数据: {json.dumps(data, indent=2)}")
            self.append_feedback(response.text)
            # 模拟延迟
            #self.root.after(1000, lambda: self.append_feedback(f"{description} 发送成功"))
            
        except Exception as e:
            self.append_feedback(f"发送HTTP请求时出错: {str(e)}")
            
    def send_serial_data(self, data, description):
        """通过串口发送数据"""
        if not self.ser or not self.serial_running:
            messagebox.showerror("错误", "串口未连接")
            return
            
        try:
            # 将数据转换为字符串格式
            data_str = json.dumps(data) + "\n"
            self.ser.write(data_str.encode('utf-8'))
            self.append_feedback(f"通过串口发送: {data_str.strip()}")
            
        except Exception as e:
            self.append_feedback(f"串口发送错误: {str(e)}")
            
    def reset_all_parameters(self):
        """重置所有参数到默认值"""
        for i in range(1, 4):
            getattr(self, f"pid{i}_kp").set(1.0)
            getattr(self, f"pid{i}_ki").set(0.1)
            getattr(self, f"pid{i}_kd").set(0.05)
            getattr(self, f"pid{i}_min").set(10)
            
        self.append_feedback("所有参数已重置为默认值")
        
    def clear_feedback(self):
        """清空反馈文本框"""
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.config(state=tk.DISABLED)
        
    def on_closing(self):
        """应用程序关闭时的清理工作"""
        if self.ser and self.serial_running:
            self.disconnect_serial()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedPIDControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    Inited = True
    root.mainloop()