import sys
import multiprocessing
# 导入模块
import main      # 对应 main.py
import main_gui  # 对应 main_gui.py

def entry_point():
    multiprocessing.freeze_support()

    args = sys.argv

    # 如果有参数 "detect"，调用 main.py 的逻辑
    if len(args) > 1 and args[1] == "detect":
        try:
            main.main_entry()  # <--- 调用修改后的函数名
        except Exception as e:
            print(f"ERROR: {e}")
            
    # 否则启动 GUI
    else:
        main_gui.gui_entry()   # <--- 调用修改后的函数名

if __name__ == "__main__":
    entry_point()