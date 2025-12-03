import sys
import time
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import threading

# --- 1. 路径与环境导入 ---
current_file_path = Path(__file__).resolve()
exp_dir = current_file_path.parent
root_path = current_file_path.parent.parent
sys.path.append(str(root_path))

try:
    from common import Camera
    # 导入 main.py 中的核心类和函数，复用逻辑
    from main import ConfigManager, fix_iccp_warning, run_detection_once
except ImportError as e:
    messagebox.showerror("错误", f"导入模块失败: {e}\n请确保 main.py 和 common 文件夹在正确位置。")
    sys.exit(1)

class DetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("工业视觉识别终端 (GUI版)")
        
        # --- 窗口自适应最大化 ---
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        try:
            self.root.state('zoomed')
        except:
            self.root.geometry(f"{int(self.screen_width*0.9)}x{int(self.screen_height*0.9)}")

        # 初始化配置
        self.config_path = exp_dir / "config.yaml"
        self.cfg_mgr = ConfigManager(self.config_path)
        
        # 相机对象
        self.camera = None
        self.is_camera_open = False

        self.setup_ui()
        
        # 启动时自动连接相机 (使用线程防止界面卡死)
        threading.Thread(target=self.connect_camera, daemon=True).start()

    def setup_ui(self):
        # 1. 顶部控制栏
        ctrl_frame = ttk.LabelFrame(self.root, text="操作面板")
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # 动态生成颜色按钮
        colors = self.cfg_mgr.config.get('colors', {}).keys()
        
        ttk.Label(ctrl_frame, text="点击进行识别: ").pack(side=tk.LEFT, padx=10)
        
        for color in colors:
            btn = ttk.Button(ctrl_frame, text=f"识别 {color.upper()}", 
                             command=lambda c=color: self.perform_detection(c))
            btn.pack(side=tk.LEFT, padx=5, pady=10)

        # 状态标签
        self.lbl_status = ttk.Label(ctrl_frame, text="正在初始化相机...", foreground="blue")
        self.lbl_status.pack(side=tk.RIGHT, padx=20)

        # 2. 图片显示区域
        img_frame = ttk.Frame(self.root)
        img_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 使用 Label 显示图片
        self.lbl_image = ttk.Label(img_frame, text="等待采集图像...", anchor="center", background="#333", foreground="white")
        self.lbl_image.pack(fill=tk.BOTH, expand=True)

    def connect_camera(self):
        try:
            self.camera = Camera.Camera()
            # 预热一下
            self.camera.getCameraData()
            self.is_camera_open = True
            self.update_status("相机已连接，就绪", "green")
        except Exception as e:
            self.update_status(f"相机连接失败: {e}", "red")

    def update_status(self, text, color="black"):
        """线程安全的更新 UI"""
        self.lbl_status.config(text=text, foreground=color)

    def perform_detection(self, task_mode):
        if not self.is_camera_open:
            messagebox.showwarning("警告", "相机尚未连接或初始化失败！")
            return

        self.update_status(f"正在执行: {task_mode} ...", "blue")
        
        # 在主线程更新 UI 会卡顿，稍微延时一下执行逻辑
        self.root.after(10, lambda: self._process_logic(task_mode))

    def _process_logic(self, task_mode):
        try:
            # 1. 获取图像
            raw_image = self.camera.getCameraData()
            if raw_image is None:
                self.update_status("取图失败", "red")
                return

            image = fix_iccp_warning(raw_image)

            # 2. 临时修改配置中的 current_task (只修改内存中的配置对象，不改文件，速度快)
            self.cfg_mgr.config['system']['current_task'] = task_mode

            # 3. 调用 main.py 中的核心函数
            # result 包含: (save_path, cx, cy)
            result_path, cx, cy = run_detection_once(image, self.cfg_mgr.config)

            # 4. 显示结果
            if result_path and result_path != "NOT_FOUND":
                self.update_status(f"识别成功! 坐标: ({cx}, {cy}) | 保存至: {result_path}", "green")
                # 加载刚才保存的图片来显示 (因为上面画了框)
                # 注意：OpenCV imread 读取的是 BGR，显示需要 RGB
                display_img = cv2.imread(result_path)
                self.display_image_on_gui(display_img)
            else:
                self.update_status(f"未识别到 {task_mode}", "orange")
                # 即使没识别到，也显示原图
                self.display_image_on_gui(image)

        except Exception as e:
            self.update_status(f"处理异常: {e}", "red")
            print(e)

    def display_image_on_gui(self, cv_image):
        """核心功能：自适应屏幕显示图片"""
        if cv_image is None: return

        # 1. 获取图片尺寸
        img_h, img_w = cv_image.shape[:2]

        # 2. 获取当前显示区域的可用尺寸 (预留边距)
        # 如果窗口刚启动，winfo_width 可能不准，用屏幕尺寸做保底
        win_w = self.root.winfo_width()
        win_h = self.root.winfo_height()
        if win_w < 100: win_w = self.screen_width
        if win_h < 100: win_h = self.screen_height

        # 预留给顶部按钮栏和边框的空间
        max_w = win_w - 40
        max_h = win_h - 150 

        # 3. 计算缩放比例 (保持长宽比)
        scale = min(max_w / img_w, max_h / img_h, 1.0) # 只缩小不放大

        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        # 4. 缩放
        resized_img = cv2.resize(cv_image, (new_w, new_h))

        # 5. 转换格式 BGR -> RGB -> ImageTk
        img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tk_img = ImageTk.PhotoImage(image=pil_img)

        # 6. 更新 Label
        self.lbl_image.config(image=tk_img, text="")
        self.lbl_image.image = tk_img # 必须保持引用，否则会被垃圾回收

    def on_close(self):
        if self.camera and hasattr(self.camera, 'CloseCamera'):
            self.camera.CloseCamera()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = DetectionGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()