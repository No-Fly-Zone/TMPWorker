import tkinter as tk
from tkinter import ttk, filedialog, messagebox
# from PIL import Image, ImageTk
# import configparser

# from logic.modules import TmpFile, PalFile
# import logic.image as impt
# import logic.render as render

from pathlib import Path
import sys


from gui.Page1 import Tab_One
from gui.Page2 import Tab_Two
from gui.Page3 import Tab_Three

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


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None

        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 25

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)   # 去掉窗口边框
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            background="#ffffff",
            relief="solid",
            borderwidth=1,
            justify="left"
        )
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ---------------- 标签页类 ----------------

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("神秘东西")
        self.geometry("800x720")

        notebook = ttk.Notebook(self)
        notebook.place(x=10, y=10, width=780, height=600)

        # 第一标签页
        self.tab_1 = Tab_One(notebook, self.append_log)
        notebook.add(self.tab_1, text="导出图像")

        # 第二标签页
        self.tab_2 = Tab_Two(notebook, self.append_log)
        notebook.add(self.tab_2, text="导入图像")

        # 第三标签页
        self.tab_3 = Tab_Three(notebook, self.append_log)
        notebook.add(self.tab_3, text="气候转换")

        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self._init_log()

    def _init_log(self):
        log_frame = ttk.Frame(self)
        log_frame.place(x=20, y=450, width=760, height=250)

        ttk.Label(log_frame, text="Log:", relief="flat").pack(anchor=tk.W)

        self.txt_log = tk.Text(log_frame, height=6, font=10,
                               state=tk.DISABLED, wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)
        self.txt_log.tag_config(
            "INFO", foreground="#858585", font=("SimSun", 10))
        self.txt_log.tag_config(
            "WARN", foreground="orange", font=("SimSun", 10))
        self.txt_log.tag_config("ERROR", foreground="red",
                                font=("SimSun", 10))
        self.txt_log.tag_config(
            "SUCCESS", foreground="#36BB53", font=("SimSun", 10))
        self.txt_log.tag_config(
            "PASS", foreground="#858585", font=("SimSun", 6))

    def append_log(self, msg, level="INFO"):
        self.txt_log.config(state=tk.NORMAL)
        if level != "PASS":
            self.txt_log.insert(tk.END, "[" + level + "]" + msg + "\n", level)
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
