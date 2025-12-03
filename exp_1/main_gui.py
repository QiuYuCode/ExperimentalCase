import sys
import cv2
import yaml
import time
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path

# --- 1. 路径设置 ---
current_file_path = Path(__file__).resolve()
exp_dir = current_file_path.parent          # D:\ExperimentalCase\exp_1
root_path = current_file_path.parent.parent # D:\ExperimentalCase
sys.path.append(str(root_path))             # 将根目录加入路径，以便导入 common

config_path = exp_dir / "config.yaml"

# --- 导入核心模块 ---
try:
    from common import Camera
    # 导入 main.py 中的核心函数
    from main import run_detection_once, fix_iccp_warning
except ImportError as e:
    messagebox.showerror("启动错误", f"缺失必要模块: {e}\n请检查 common 文件夹是否在 {root_path}")
    sys.exit(1)

# =============================================================================
#  UI 样式配置
# =============================================================================
COLORS = {
    "bg_dark": "#2c3e50",       # 侧边栏背景
    "bg_light": "#ecf0f1",      # 内容区背景
    "btn_normal": "#34495e",    # 按钮默认
    "btn_hover": "#1abc9c",     # 按钮悬停
    "text_light": "#ffffff",    # 浅色文字
    "accent": "#e74c3c"         # 强调色
}

class ModernApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("工业视觉一体化工作站")
        
        # 窗口自适应最大化
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        try:
            self.state('zoomed')
        except:
            self.geometry(f"{int(screen_w*0.9)}x{int(screen_h*0.9)}")

        # 初始化共享资源
        self.camera = None
        self.config_data = {}
        self.load_config()
        
        # --- 【修复重点】先初始化状态变量，再构建 UI ---
        self.camera_status_var = tk.StringVar(value="正在连接相机...")
        
        # 初始化 UI
        self.setup_layout()
        
        # 异步连接相机
        threading.Thread(target=self.connect_camera_thread, daemon=True).start()

    def load_config(self):
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
        else:
            self.config_data = {'colors': {}, 'system': {}}

    def connect_camera_thread(self):
        try:
            self.camera = Camera.Camera()
            # 预热取图
            raw = self.camera.getCameraData()
            if raw is not None:
                self.camera_status_var.set("相机已连接")
            else:
                self.camera_status_var.set("相机连接成功但无数据")
                
            # 通知子页面相机就绪 (如果有回调需求)
            self.page_detect.update_camera_status(True)
            self.page_tune.update_camera_status(True)
        except Exception as e:
            self.camera_status_var.set(f"相机连接失败: {e}")

    def setup_layout(self):
        # 1. 侧边导航栏
        self.sidebar = tk.Frame(self, bg=COLORS["bg_dark"], width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False) # 固定宽度

        # 标题
        lbl_title = tk.Label(self.sidebar, text="VISION\nSYSTEM", bg=COLORS["bg_dark"], 
                             fg=COLORS["text_light"], font=("Arial", 20, "bold"), pady=30)
        lbl_title.pack(side=tk.TOP)

        # 导航按钮
        self.create_nav_btn("🔍 智能识别", self.show_detection_page)
        self.create_nav_btn("⚙️ 参数调试", self.show_tuning_page)
        
        # 底部状态 (现在 self.camera_status_var 已经存在了，不会报错)
        lbl_status = tk.Label(self.sidebar, textvariable=self.camera_status_var, 
                              bg=COLORS["bg_dark"], fg="#95a5a6", wraplength=180, justify="center")
        lbl_status.pack(side=tk.BOTTOM, pady=20)

        # 2. 内容区域容器
        self.content_area = tk.Frame(self, bg=COLORS["bg_light"])
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 3. 初始化子页面
        self.page_detect = DetectionPage(self.content_area, self)
        self.page_tune = TuningPage(self.content_area, self)
        
        # 默认显示识别页
        self.show_detection_page()

    def create_nav_btn(self, text, command):
        btn = tk.Button(self.sidebar, text=text, bg=COLORS["bg_dark"], fg=COLORS["text_light"],
                        font=("微软雅黑", 12), bd=0, activebackground=COLORS["btn_hover"],
                        activeforeground=COLORS["text_light"], cursor="hand2", command=command, pady=15)
        btn.pack(side=tk.TOP, fill=tk.X)
        
        # 简单的悬停效果
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["btn_normal"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["bg_dark"]))

    def show_detection_page(self):
        self.page_tune.pack_forget()
        self.page_detect.pack(fill=tk.BOTH, expand=True)
        # 切换回来时，重新加载配置
        self.load_config()
        self.page_detect.refresh_buttons()

    def show_tuning_page(self):
        self.page_detect.pack_forget()
        self.page_tune.pack(fill=tk.BOTH, expand=True)
        self.page_tune.grab_live_frame() 

    def on_close(self):
        if self.camera and hasattr(self.camera, 'CloseCamera'):
            self.camera.CloseCamera()
        self.destroy()

# =============================================================================
#  页面 1: 智能识别
# =============================================================================
class DetectionPage(tk.Frame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, bg=COLORS["bg_light"])
        self.app = app_controller
        self.setup_ui()

    def setup_ui(self):
        # 顶部控制栏
        top_bar = tk.Frame(self, bg="white", height=60)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=20, pady=20)
        
        tk.Label(top_bar, text="当前任务:", bg="white", font=("微软雅黑", 12)).pack(side=tk.LEFT, padx=10)
        
        self.btn_container = tk.Frame(top_bar, bg="white")
        self.btn_container.pack(side=tk.LEFT)
        
        self.lbl_result = tk.Label(top_bar, text="等待指令...", bg="white", fg="gray", font=("微软雅黑", 12, "bold"))
        self.lbl_result.pack(side=tk.RIGHT, padx=20)

        # 图片显示区
        self.img_label = tk.Label(self, bg="#bdc3c7", text="无图像信号")
        self.img_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    def refresh_buttons(self):
        for widget in self.btn_container.winfo_children():
            widget.destroy()
        
        colors = self.app.config_data.get('colors', {}).keys()
        for color in colors:
            btn = ttk.Button(self.btn_container, text=f"检测 {color.upper()}", 
                             command=lambda c=color: self.perform_detection(c))
            btn.pack(side=tk.LEFT, padx=5)

    def update_camera_status(self, is_ready):
        if is_ready:
            self.img_label.config(text="相机就绪，请选择任务")

    def perform_detection(self, task_mode):
        if not self.app.camera:
            messagebox.showwarning("警告", "相机尚未连接")
            return
        
        raw_img = self.app.camera.getCameraData()
        if raw_img is None:
            self.lbl_result.config(text="取图失败", fg="red")
            return
        
        image = fix_iccp_warning(raw_img)
        
        self.app.config_data['system']['current_task'] = task_mode
        path, cx, cy = run_detection_once(image, self.app.config_data)
        
        if path and path != "NOT_FOUND":
            self.lbl_result.config(text=f"成功: {task_mode} ({cx}, {cy})", fg="green")
            res_img = cv2.imread(path)
            if res_img is not None:
                self.display_image(res_img)
            else:
                # 假如路径有特殊字符读取失败，显示原图
                self.display_image(image)
        else:
            self.lbl_result.config(text=f"未找到 {task_mode}", fg="#e67e22")
            self.display_image(image)

    def display_image(self, cv_img):
        h, w = cv_img.shape[:2]
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        if win_w < 100: win_w = 800
        if win_h < 100: win_h = 600

        scale = min((win_w-40)/w, (win_h-100)/h, 1.0)
        new_w, new_h = int(w*scale), int(h*scale)
        
        img_rgb = cv2.cvtColor(cv2.resize(cv_img, (new_w, new_h)), cv2.COLOR_BGR2RGB)
        tk_img = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
        
        self.img_label.config(image=tk_img, text="")
        self.img_label.image = tk_img

# =============================================================================
#  页面 2: 参数调试
# =============================================================================
class TuningPage(tk.Frame):
    def __init__(self, parent, app_controller):
        super().__init__(parent, bg=COLORS["bg_light"])
        self.app = app_controller
        self.current_img = None
        self.h_min = tk.IntVar(); self.h_max = tk.IntVar(value=180)
        self.s_min = tk.IntVar(); self.s_max = tk.IntVar(value=255)
        self.v_min = tk.IntVar(); self.v_max = tk.IntVar(value=255)
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)

        img_container = tk.Frame(self, bg="black")
        img_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.canvas = tk.Canvas(img_container, bg="#222", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click_image)
        
        ctrl_panel = tk.Frame(self, bg="white")
        ctrl_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        ttk.Label(ctrl_panel, text="HSV 参数调节", font=("bold", 14)).pack(pady=10)
        ttk.Button(ctrl_panel, text="📸 重新抓拍图像", command=self.grab_live_frame).pack(fill=tk.X, padx=10, pady=5)
        
        self.create_slider(ctrl_panel, "H Min", self.h_min, 0, 180)
        self.create_slider(ctrl_panel, "H Max", self.h_max, 0, 180)
        self.create_slider(ctrl_panel, "S Min", self.s_min, 0, 255)
        self.create_slider(ctrl_panel, "S Max", self.s_max, 0, 255)
        self.create_slider(ctrl_panel, "V Min", self.v_min, 0, 255)
        self.create_slider(ctrl_panel, "V Max", self.v_max, 0, 255)

        ttk.Separator(ctrl_panel, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        ttk.Label(ctrl_panel, text="保存至配置文件:").pack(pady=5)
        
        self.combo_target = ttk.Combobox(ctrl_panel, state="readonly")
        self.combo_target.pack(fill=tk.X, padx=10)
        self.combo_target.bind("<Button-1>", self.refresh_target_list)
        
        ttk.Button(ctrl_panel, text="💾 保存参数", command=self.save_config).pack(fill=tk.X, padx=10, pady=10)
        
        self.lbl_preview = tk.Label(ctrl_panel, text="下方为处理结果预览", bg="white", fg="gray")
        self.lbl_preview.pack(side=tk.BOTTOM, pady=10)
        self.panel_res = tk.Label(ctrl_panel, bg="#eee")
        self.panel_res.pack(side=tk.BOTTOM, fill=tk.X, padx=10)

    def create_slider(self, parent, label, var, min_v, max_v):
        f = tk.Frame(parent, bg="white")
        f.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(f, text=label, bg="white", width=5).pack(side=tk.LEFT)
        tk.Scale(f, from_=min_v, to=max_v, orient=tk.HORIZONTAL, variable=var, 
                 showvalue=0, command=lambda x: self.update_view()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(f, textvariable=var, bg="white", width=3).pack(side=tk.RIGHT)

    def update_camera_status(self, is_ready):
        pass

    def grab_live_frame(self):
        if not self.app.camera: return
        raw = self.app.camera.getCameraData()
        if raw is not None:
            self.current_img = fix_iccp_warning(raw)
            self.update_view()

    def update_view(self):
        if self.current_img is None: return
        
        lower = np.array([self.h_min.get(), self.s_min.get(), self.v_min.get()])
        upper = np.array([self.h_max.get(), self.s_max.get(), self.v_max.get()])
        
        hsv = cv2.cvtColor(self.current_img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        res = cv2.bitwise_and(self.current_img, self.current_img, mask=mask)
        
        # 混合显示红色 Mask
        colored_mask = np.zeros_like(self.current_img)
        colored_mask[:,:] = [0, 0, 255] 
        masked_overlay = cv2.bitwise_and(colored_mask, colored_mask, mask=mask)
        display_main = cv2.addWeighted(self.current_img, 1, masked_overlay, 0.5, 0)
        
        self.show_image(display_main, self.canvas)
        self.show_image(res, self.panel_res, is_preview=True)

    def show_image(self, cv_img, widget, is_preview=False):
        h, w = cv_img.shape[:2]
        if is_preview:
            target_w = 200
            scale = target_w / w
        else:
            win_w = widget.winfo_width()
            win_h = widget.winfo_height()
            if win_w < 10: win_w = 800; win_h = 600
            scale = min(win_w/w, win_h/h)
            
        new_w, new_h = int(w*scale), int(h*scale)
        img_rgb = cv2.cvtColor(cv2.resize(cv_img, (new_w, new_h)), cv2.COLOR_BGR2RGB)
        tk_img = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
        
        if isinstance(widget, tk.Canvas):
            widget.delete("all")
            cx, cy = win_w//2, win_h//2
            widget.create_image(cx, cy, anchor=tk.CENTER, image=tk_img)
            widget.image = tk_img
            self.img_scale = scale
            self.img_offset = (cx - new_w//2, cy - new_h//2)
        else:
            widget.config(image=tk_img)
            widget.image = tk_img

    def on_click_image(self, event):
        if self.current_img is None: return
        ox, oy = self.img_offset
        ix = int((event.x - ox) / self.img_scale)
        iy = int((event.y - oy) / self.img_scale)
        
        if 0 <= ix < self.current_img.shape[1] and 0 <= iy < self.current_img.shape[0]:
            pixel = self.current_img[iy, ix]
            hsv = cv2.cvtColor(np.uint8([[pixel]]), cv2.COLOR_BGR2HSV)[0][0]
            
            self.h_min.set(max(0, hsv[0]-10)); self.h_max.set(min(180, hsv[0]+10))
            self.s_min.set(max(0, hsv[1]-50)); self.s_max.set(255)
            self.v_min.set(max(0, hsv[2]-50)); self.v_max.set(255)
            self.update_view()

    def refresh_target_list(self, event=None):
        targets = []
        for k, v in self.app.config_data.get('colors', {}).items():
            if 'lower' in v: targets.append(k)
            if 'lower1' in v: targets.append(f"{k} (区间1)")
            if 'lower2' in v: targets.append(f"{k} (区间2)")
        self.combo_target['values'] = targets

    def save_config(self):
        target = self.combo_target.get()
        if not target:
            messagebox.showwarning("提示", "请选择保存目标")
            return
            
        lower = [self.h_min.get(), self.s_min.get(), self.v_min.get()]
        upper = [self.h_max.get(), self.s_max.get(), self.v_max.get()]
        
        color_key = target.split(" (")[0]
        suffix = ""
        if "区间" in target:
            suffix = target.split("区间")[1].replace(")", "")
            
        key_l, key_u = f"lower{suffix}", f"upper{suffix}"
        
        self.app.config_data['colors'][color_key][key_l] = lower
        self.app.config_data['colors'][color_key][key_u] = upper
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.app.config_data, f, allow_unicode=True, sort_keys=False)
            messagebox.showinfo("成功", f"参数已保存到 {target}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

if __name__ == "__main__":
    app = ModernApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()