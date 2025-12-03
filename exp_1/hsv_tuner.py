import sys
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import yaml
import time

# --- 1. 路径与环境设置 ---
current_file_path = Path(__file__).resolve()
exp_dir = current_file_path.parent
root_path = current_file_path.parent.parent
sys.path.append(str(root_path))
config_path = exp_dir / "config.yaml"

try:
    from common import Camera
except ImportError:
    print("ERROR: 找不到 common 模块，请检查目录结构")
    sys.exit(1)

class HSVCalibrator:
    def __init__(self, root):
        self.root = root
        self.root.title("HSV 阈值调试工具 (适配 Config.yaml)")
        
        # --- 窗口自适应 ---
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        try:
            self.root.state('zoomed')
        except:
            self.root.geometry(f"{int(screen_width*0.9)}x{int(screen_height*0.9)}")

        # 初始化 HSV 变量
        self.h_min = tk.IntVar(value=0)
        self.s_min = tk.IntVar(value=0)
        self.v_min = tk.IntVar(value=0)
        self.h_max = tk.IntVar(value=180)
        self.s_max = tk.IntVar(value=255)
        self.v_max = tk.IntVar(value=255)

        # 加载配置
        self.config_data = self.load_yaml_config()
        self.target_list = self.parse_color_targets()

        # 加载图像
        self.original_cv_image = self.capture_image()
        if self.original_cv_image is None:
            messagebox.showerror("错误", "无法连接相机或获取图像！")
            sys.exit()

        # --- 计算缩放比例 ---
        img_h, img_w = self.original_cv_image.shape[:2]
        # 计算适合屏幕显示的尺寸 (预留控制面板空间)
        max_w = (screen_width - 100) / 3
        max_h = screen_height - 350
        scale = min(max_w / img_w, max_h / img_h, 1.0)
        
        self.resize_dim = (int(img_w * scale), int(img_h * scale))
        self.display_image = cv2.resize(self.original_cv_image, self.resize_dim)

        self.setup_ui()
        self.update_result()

    def load_yaml_config(self):
        """加载 YAML 配置文件"""
        if not config_path.exists():
            messagebox.showerror("错误", f"找不到配置文件: {config_path}")
            sys.exit()
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def parse_color_targets(self):
        """解析配置文件，识别单区间和双区间"""
        targets = []
        if 'colors' not in self.config_data:
            return targets
        
        for color_name, params in self.config_data['colors'].items():
            # 情况1: 普通单区间 (如 yellow)
            if 'lower' in params:
                targets.append(color_name)
            
            # 情况2: 双区间 (如 red)
            # 这种结构下，red 会生成两个选项供分别调试
            if 'lower1' in params:
                targets.append(f"{color_name} (区间1)")
            if 'lower2' in params:
                targets.append(f"{color_name} (区间2)")
        return targets

    def capture_image(self):
        print("正在连接相机取图...")
        cam = None
        try:
            cam = Camera.Camera()
            time.sleep(0.5) # 等待曝光稳定
            raw_img = cam.getCameraData()
            if raw_img is not None:
                # 修复 libpng 警告并转码
                _, encoded_img = cv2.imencode('.jpg', raw_img)
                return cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"相机错误: {e}")
        finally:
            if cam and hasattr(cam, 'CloseCamera'):
                cam.CloseCamera()
        return None

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 上部：图片显示 ===
        img_container = ttk.Frame(main_frame)
        img_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 1. 原图
        f1 = ttk.Frame(img_container)
        f1.pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Label(f1, text="1. 原图 (点击吸色)").pack()
        self.cvs_orig = tk.Canvas(f1, width=self.resize_dim[0], height=self.resize_dim[1], bg="#222")
        self.cvs_orig.pack()
        self.cvs_orig.bind("<Button-1>", self.on_click_image)

        # 2. Mask
        f2 = ttk.Frame(img_container)
        f2.pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Label(f2, text="2. Mask 预览 (黑白)").pack()
        self.pnl_mask = tk.Label(f2, bg="#222")
        self.pnl_mask.pack()

        # 3. 结果
        f3 = ttk.Frame(img_container)
        f3.pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Label(f3, text="3. 最终识别结果").pack()
        self.pnl_res = tk.Label(f3, bg="#222")
        self.pnl_res.pack()

        # === 下部：控制与保存 ===
        ctrl_frame = ttk.LabelFrame(main_frame, text="参数调节")
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # 滑块区
        slider_frame = ttk.Frame(ctrl_frame)
        slider_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)

        self.create_slider(slider_frame, "H Min", self.h_min, 0, 180, 0, 0)
        self.create_slider(slider_frame, "S Min", self.s_min, 0, 255, 1, 0)
        self.create_slider(slider_frame, "V Min", self.v_min, 0, 255, 2, 0)
        
        self.create_slider(slider_frame, "H Max", self.h_max, 0, 180, 0, 1)
        self.create_slider(slider_frame, "S Max", self.s_max, 0, 255, 1, 1)
        self.create_slider(slider_frame, "V Max", self.v_max, 0, 255, 2, 1)

        # 保存区
        save_frame = ttk.Frame(ctrl_frame)
        save_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=10)

        ttk.Label(save_frame, text="保存至 Config 的哪个目标?").pack(anchor=tk.W)
        self.combo_target = ttk.Combobox(save_frame, values=self.target_list, state="readonly", width=25)
        if self.target_list: self.combo_target.current(0)
        self.combo_target.pack(pady=5)

        ttk.Button(save_frame, text="💾 保存并更新 Config.yaml", command=self.save_to_yaml).pack(fill=tk.X, pady=5)
        self.lbl_status = ttk.Label(save_frame, text="就绪", foreground="gray")
        self.lbl_status.pack()

    def create_slider(self, parent, label, variable, min_val, max_val, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col*2, sticky=tk.W, pady=5)
        tk.Scale(parent, from_=min_val, to=max_val, orient=tk.HORIZONTAL, 
                 variable=variable, length=220, command=lambda x: self.update_result()).grid(row=row, column=col*2+1, padx=10)

    def on_click_image(self, event):
        """点击吸色功能"""
        x, y = event.x, event.y
        if x >= self.resize_dim[0] or y >= self.resize_dim[1]: return

        bgr = self.display_image[y, x]
        hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
        print(f"吸色: H={h}, S={s}, V={v}")

        # 自动设定范围 (H±10, SV宽松一些)
        self.h_min.set(max(0, h - 10))
        self.h_max.set(min(180, h + 10))
        self.s_min.set(max(0, s - 60))
        self.s_max.set(255)
        self.v_min.set(max(0, v - 60))
        self.v_max.set(255)
        self.update_result()

    def update_result(self):
        """刷新图像显示"""
        lower = np.array([self.h_min.get(), self.s_min.get(), self.v_min.get()])
        upper = np.array([self.h_max.get(), self.s_max.get(), self.v_max.get()])

        hsv = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        result = cv2.bitwise_and(self.display_image, self.display_image, mask=mask)

        # 刷新 UI
        if not hasattr(self, 'tk_orig'):
            im_rgb = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
            self.tk_orig = ImageTk.PhotoImage(image=Image.fromarray(im_rgb))
            self.cvs_orig.create_image(0, 0, anchor=tk.NW, image=self.tk_orig)

        im_mask = Image.fromarray(mask)
        tk_mask = ImageTk.PhotoImage(image=im_mask)
        self.pnl_mask.config(image=tk_mask)
        self.pnl_mask.image = tk_mask

        im_res = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        tk_res = ImageTk.PhotoImage(image=Image.fromarray(im_res))
        self.pnl_res.config(image=tk_res)
        self.pnl_res.image = tk_res

    def save_to_yaml(self):
        """保存逻辑：精准匹配 yellow/red 区间"""
        target_str = self.combo_target.get()
        if not target_str:
            messagebox.showwarning("警告", "请选择保存目标！")
            return

        # 准备数据 (list格式，方便yaml写入)
        lower_val = [self.h_min.get(), self.s_min.get(), self.v_min.get()]
        upper_val = [self.h_max.get(), self.s_max.get(), self.v_max.get()]

        try:
            # 1. 重新读取最新配置 (防止覆盖 system 字段)
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 2. 解析目标键值
            # 目标字符串可能是 "yellow" 或 "red (区间1)"
            color_key = target_str
            key_lower = "lower"
            key_upper = "upper"

            if "(区间" in target_str:
                parts = target_str.split(" (")
                color_key = parts[0] # "red"
                # "区间2)" -> "2"
                idx = parts[1].replace("区间", "").replace(")", "")
                key_lower = f"lower{idx}"
                key_upper = f"upper{idx}"

            # 3. 验证并更新
            if color_key in config['colors']:
                config['colors'][color_key][key_lower] = lower_val
                config['colors'][color_key][key_upper] = upper_val
            else:
                messagebox.showerror("错误", f"配置文件中没有颜色: {color_key}")
                return

            # 4. 写回文件 (使用 allow_unicode 保持中文注释不乱码，虽然注释可能会丢)
            with open(config_path, 'w', encoding='utf-8') as f:
                # default_flow_style=None 让列表可能显示为 flow 风格 [a,b,c]，更紧凑
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)

            self.lbl_status.config(text=f"已保存: {target_str}", foreground="green")
            messagebox.showinfo("成功", f"参数已更新！\n\n{key_lower}: {lower_val}\n{key_upper}: {upper_val}")

        except Exception as e:
            messagebox.showerror("保存失败", str(e))

def main():
    root = tk.Tk()
    app = HSVCalibrator(root)
    root.mainloop()

if __name__ == "__main__":
    main()