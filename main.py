import tkinter as tk
from tkinter import ttk, filedialog, messagebox
# from PIL import Image, ImageTk
# import configparser

# from logic.modules import TmpFile, PalFile
# import logic.image as impt
# import logic.render as render

from pathlib import Path
import sys
from datetime import datetime

from gui.Page1 import Tab_One
from gui.Page2 import Tab_Two
from gui.Page3 import Tab_Three
from gui.Page4 import Tab_Four

# pyinstaller -w main.py


def get_base_path():
    if getattr(sys, "frozen", False):
        # PyInstaller onefile 解压目录
        return sys._MEIPASS
    return Path(__file__).resolve().parent

# ---------------- 配置 ----------------


def get_resource_path():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return Path(__file__).resolve().parent


def get_app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
CONFIG_DIR = Path(APP_DIR) / "config"
CONFIG_FILE = "files_config.ini"
CONFIG_PATH = Path(CONFIG_DIR) / CONFIG_FILE

# ---------------- 全局变量 ----------------
# lst_files = []
# lst_state = []
# pal_path = None
# img = None

# ---------------- 提示框 ----------------

# ---------------- 标签页类 ----------------


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("TMP 转换")
        self.geometry("920x864")

        notebook = ttk.Notebook(self)
        notebook.place(x=10, y=10, width=900, height=670)

        # 第一标签页
        self.tab_1 = Tab_One(notebook, self.append_log)
        notebook.add(self.tab_1, text="导出图像")

        # 第二标签页
        self.tab_2 = Tab_Two(notebook, self.append_log)
        notebook.add(self.tab_2, text="导入图像")

        # 第三标签页
        self.tab_3 = Tab_Three(notebook, self.append_log)
        notebook.add(self.tab_3, text="气候转换")

        # 第四标签页
        self.tab_4 = Tab_Four(notebook, self.append_log)
        notebook.add(self.tab_4, text="图像切块")

        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self._init_log()

    def _init_log(self):
        log_frame = ttk.Frame(self)
        log_frame.place(x=10, y=680, width=900, height=184)

        ttk.Label(log_frame, text="Log:", relief="flat").place(
            x=10, y=0, width=80,  height=20)

        self.txt_log = tk.Text(log_frame, height=6, font=10,
                               state=tk.DISABLED, wrap=tk.WORD)
        self.txt_log.place(x=5, y=24, width=850,  height=150)

        self.txt_log.tag_config(
            "INFO", foreground="#858585", font=("SimSun", 10))
        self.txt_log.tag_config(
            "WARN", foreground="#FFAA00", font=("SimSun", 10))
        self.txt_log.tag_config(
            "ERROR", foreground="#FF0000", font=("SimSun", 10))
        self.txt_log.tag_config(
            "SUCCESS", foreground="#36BB53", font=("SimSun", 10))
        self.txt_log.tag_config(
            "PASS", foreground="#858585", font=("SimSun", 6))
        self.txt_log.tag_config(
            "TIME", foreground="#999999", font=("SimSun", 10))

        sb2 = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                            command=self.txt_log.yview)

        sb2.place(x=855, y=24, height=150)
        self.txt_log.config(yscrollcommand=sb2.set)

    def append_log(self, msg, level="INFO"):
        self.txt_log.config(state=tk.NORMAL)
        if level != "PASS":
            # ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[2:-3]

            self.txt_log.insert(tk.END, f"[{ts}] ", "TIME")
            self.txt_log.insert(tk.END, f"[{level}] ", level)
            self.txt_log.insert(tk.END, msg + "\n", level)
        else:
            self.txt_log.insert(tk.END, "\n", level)

        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)
        self.txt_log.update_idletasks()

    def on_tab_changed(self, event):
        notebook = event.widget
        current_frame = notebook.nametowidget(notebook.select())

        if hasattr(current_frame, "load_config"):
            current_frame.load_config()


if __name__ == "__main__":
    app = App()
    app.mainloop()
