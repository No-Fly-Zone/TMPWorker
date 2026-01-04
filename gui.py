import tkinter as tk
import os
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import configparser

from logic.modules import TmpFile, PalFile
import logic.image as impt
import logic.render as render

from pathlib import Path
import sys
import os

def get_base_path():
    if getattr(sys, 'frozen', False):
        # PyInstaller onefile 解压目录
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))
# ---------------- 配置 ----------------


def get_resource_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()                 # 可写
CONFIG_DIR = os.path.join(APP_DIR, "config")
CONFIG_FILE = "files_config.ini"
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
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


class FilesTab(ttk.Frame):

    def __init__(self, master, log_callback):
        super().__init__(master)
        self.log_callback = log_callback

        self.full_paths = []
        self.lst_files = []
        self.path_floder = None
        self.path_pal = None
        self.path_template = None

        self.current_image = None  # 保存 PhotoImage 引用

        self.only_start = ''
        self.only_end = ''

        self.image_label_width = 300
        self.image_label_height = 200
        self.theaters = ['.tem', '.urb', '.sno', '.ubn', '.des', '.lun']
        self._init_ui()

        self.load_config()
        self.tmp_suffix = '*'+' *'.join(self.theaters)

    def log(self, msg):
        self.log_callback(msg)

    # --------- UI ---------

    def _init_ui(self):
        self.notebookType = 0
        # ----- 文件列表
        list_frame = ttk.Frame(self)
        list_frame.place(x=10, y=10, width=250, height=370)

        self.lb_files = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED, relief='flat', takefocus=False)
        self.lb_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                           command=self.lb_files.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.lb_files.config(yscrollcommand=sb.set)

        # ----- 文件夹选择
        self.path_frame = ttk.Frame(self)
        self.path_frame.place(x=260, y=10, width=500, height=80)

        # 1) 批处理路径选择
        self.lb_floder = tk.Listbox(
            self.path_frame, selectmode=tk.SINGLE, relief='flat')
        self.lb_floder.place(x=0, y=0, width=300, height=25)

        ttk.Button(
            self.path_frame, text='选择目录', command=self.btn_choose_folder
        ).place(x=320, y=0, width=80, height=25)

        # 2) 色盘选择
        self.lb_pal = tk.Listbox(
            self.path_frame, selectmode=tk.SINGLE, relief='flat')
        self.lb_pal.place(x=0, y=30, width=300, height=25)

        ttk.Button(
            self.path_frame, text='选择pal', command=self.btn_choose_pal
        ).place(x=320, y=30, width=80, height=25)

        # 3) 模板选择
        self.lb_template = tk.Listbox(
            self.path_frame, selectmode=tk.SINGLE, relief='flat')
        self.lb_template.place(x=0, y=60, width=300, height=25)

        self.btn_template = ttk.Button(
            self.path_frame, text='选择模板', command=self.btn_choose_template
        )
        self.btn_template.place(x=320, y=60, width=80, height=25)

        # ----- 选项设置
        self.ckb_frame = ttk.Frame(self)

        # 1) Checkbox 自动色盘
        self.var_auto_pal = tk.StringVar(value='enable')

        self.ckb_auto_pal = ttk.Checkbutton(
            self.ckb_frame, text='自动色盘', variable=self.var_auto_pal, onvalue='enable', offvalue='disable')

        self.ckb_auto_pal.place(x=0, y=0, width=80, height=25)
        ToolTip(self.ckb_auto_pal, "根据 tmp文件后缀在选中色盘的文件夹中自动匹配\n格式为isoxxx.pal的色盘文件")

        # 2) Label 前缀
        self.lb_prefix = ttk.Label(self.ckb_frame, text='前缀：')
        self.lb_prefix.place(x=150, y=0, width=80, height=25)

        self.text_prefix = tk.Text(self.ckb_frame, relief='flat')
        self.text_prefix.place(x=185, y=2, width=104, height=20)
        ToolTip(self.text_prefix, "只转换带有该前缀的文件")

        # self.text_prefix.bind("<Control-v>", self.text_limit_len_CtrlV)
        # self.text_prefix.bind("<Key>", self.text_limit_len_key)

        # 3) Label 后缀
        self.lb_suffix = ttk.Label(self.ckb_frame, text='后缀：')
        self.lb_suffix.place(x=150, y=28, width=80, height=25)

        self.text_suffix = tk.Text(self.ckb_frame, relief='flat')
        self.text_suffix.place(x=185, y=30, width=104, height=20)
        ToolTip(self.text_suffix, "只转换带有该后缀的文件，包含文件后缀名\n符合该后缀的文件将跳过气候检查")

        # self.text_suffix.bind("<Control-v>", self.text_limit_len_CtrlV)
        # self.text_suffix.bind("<Key>", self.text_limit_len_key)

        # 4) Label 导出名称
        self.lb_save_name = ttk.Label(self.ckb_frame, text='导出名称：')
        self.lb_save_name.place(x=150, y=58, width=80, height=25)

        self.text_save_name = tk.Text(self.ckb_frame, relief='flat')
        self.text_save_name.place(x=208, y=60, width=81, height=20)

        # self.text_suffix.bind("<Control-v>", self.text_limit_len_CtrlV)
        # self.text_suffix.bind("<Key>", self.text_limit_len_key)

        # 按钮区
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.place(x=265, y=270, width=420, height=250)

        # 右侧预览区
        self.image_label = ttk.Label(self, anchor="center")
        self.image_label.place(
            x=365, y=210, width=self.image_label_width, height=self.image_label_height)

        self.lb_files.bind("<<ListboxSelect>>", self.file_on_select)
        self.show_preview(Image.new('RGB', (10, 10), (255, 255, 255)))

    # --------- 行为逻辑 ---------

    def get_palette(self, file_name=None):
        print(self.var_auto_pal.get())
        if self.var_auto_pal.get() == 'enable':
            pal_name = 'iso' + file_name[-3:] + '.pal'
            print(pal_name)
            pal_floder = Path(self.path_pal).parent
            pal_file = pal_floder / pal_name
            palette = PalFile(pal_file).palette
        else:
            palette = PalFile(self.path_pal).palette
        return palette

    def btn_choose_folder(self):
        floder = filedialog.askdirectory(title='选择 batch floder')
        if not floder:
            self.path_floder = ''
            self.lb_floder.delete(0, tk.END)
            self.save_config()
            return

        self.path_floder = floder
        self.lb_floder.delete(0, tk.END)
        self.lb_floder.insert(tk.END, str(floder))
        self.save_config()

    def btn_choose_pal(self):

        while True:
            pal = filedialog.askopenfilename(
                title='选择 pal 文件',    filetypes=[("PAL files", '*.pal')])
            if not pal:
                self.path_pal = ''
                self.lb_pal.delete(0, tk.END)
                self.save_config()
                return
            if pal.endswith('.pal'):
                self.path_pal = pal
                self.lb_pal.delete(0, tk.END)
                self.lb_pal.insert(tk.END, pal)
                self.save_config()
                return
            messagebox.showwarning('Warning', 'Not a pal')

    def btn_choose_template(self):
        template = filedialog.askopenfilename(title='选择文件',    filetypes=[
            ("TMP files", self.tmp_suffix)])
        if not template:
            self.path_template = ''
            self.lb_template.delete(0, tk.END)
            self.save_config()
            return
        else:
            self.path_template = template
            self.lb_template.delete(0, tk.END)
            self.lb_template.insert(tk.END, template)
            self.save_config()
            return

    def btn_add_files(self):
        files = filedialog.askopenfilenames(title='选择文件',    filetypes=[
            ("TMP files", self.tmp_suffix)])
        for f in files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, os.path.basename(f))
        self.save_config()

    def btn_remove_selected(self):
        for index in reversed(self.lb_files.curselection()):
            self.lb_files.delete(index)
            del self.full_paths[index]
        self.save_config()

    def btn_remove_all(self):
        if messagebox.askyesno("标题", "是否全部移除"):
            self.lb_files.delete(0, tk.END)
            self.full_paths.clear()
            self.save_config()

    def btn_run(self):
        pass

    # --------- 图片预览 ---------

    def file_on_select(self, event):
        if not self.lb_files.curselection():
            return

        if not Path(self.path_pal).is_file():
            return
        index = self.lb_files.curselection()[0]
        file = self.full_paths[index]

        render_img, palette = self.render_preview(file)
        self.show_preview(render_img, palette)

    # 图片预览
    def render_preview(self, file):
        export_img = file[:-4] + '.png'

        if self.var_auto_pal.get() == 'enable':
            pal_name = 'iso' + file[-3:] + '.pal'

            print(pal_name)
            pal_floder = Path(self.path_pal).parent
            pal_file = pal_floder / pal_name

            palette = PalFile(pal_file).palette
        else:
            palette = PalFile(self.path_pal).palette
        tmp = TmpFile(file)
        render_img = render.render_full_png(
            tmp, palette, export_img,
            render_extra=True,
            background_index=0, out_bmp=False, out_png=False)
        return render_img, palette

    def show_preview(self, render_img, palette = None):

        # 填充边框颜色
        border_color1 = (255, 255, 255, 255) if render_img.mode == 'RGBA' else (
            255, 255, 255)
        border_color2 = (225, 225, 225, 255) if render_img.mode == 'RGBA' else (
            225, 225, 225)

        p_width = self.image_label_width - 8
        p_height = self.image_label_height - 8

        if not palette == None:
            render_img = render_img.copy()
            pixels = render_img.load()
            old_color = palette[0]
            new_color = border_color1

            for x in range(render_img.width):
                for y in range(render_img.height):
                    if pixels[x, y] == old_color:
                        pixels[x, y] = new_color

        temp_img = Image.new(
            render_img.mode, (p_width + 2, p_height + 2), border_color1)

        w1, h1 = temp_img.size
        w2, h2 = render_img.size
        temp_img.paste(render_img, (int(0.5*(w1-w2)), int(0.5*(h1-h2))))

        preview_img = Image.new(
            render_img.mode, (p_width + 4, p_height + 4), border_color2)
        preview_img.paste(temp_img, (1, 1))

        # 根据预览大小缩放
        width, height = preview_img.size

        w = self.image_label.winfo_width()
        h = self.image_label.winfo_height()

        if width < w or height < h:
            preview_img.resize((w, h), Image.LANCZOS)

        self.current_image = ImageTk.PhotoImage(preview_img)
        self.image_label.config(image=self.current_image)

    # --------- 长度限制 ---------

    def text_limit_len_CtrlV(self, event=None):
        # 粘贴
        MAX_LEN = 15

        widget = event.widget
        content = widget.get("1.0", "end-1c")
        if len(content) > MAX_LEN:
            widget.delete("1.0", "end")
            widget.insert("1.0", content[:MAX_LEN])

    def text_limit_len_key(self, event):
        # # 限制长度
        # MAX_LEN = 15

        # if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Up", "Down"):
        #     return
        # widget = event.widget

        # content = widget.get("1.0", "end-1c")
        # if len(content) >= MAX_LEN:
        #     return "break"
        pass

    # --------- 配置读写 ---------

    def save_config(self):
        SECTION_FILE = 'Files'
        TMPPATH_NAME = 'TmpPath'
        IMAGEPATH_NAME = 'ImagePath'

        SECTION_PATH = 'Paths'
        PAL_NAME = 'Palette'
        FLODER_NAME = 'FileFloder'
        TEMPLATE_NAME = 'Template'

        SECTION_SETTING = 'Settings'
        AUTOPAL_NAME = 'AutoPal'
        THEATER_NAME = 'Theater'

        os.makedirs(CONFIG_DIR, exist_ok=True)
        config = configparser.ConfigParser()
        config.optionxform = str
        if Path(CONFIG_PATH).is_file():
            config.read(CONFIG_PATH, encoding="utf-8")

        if not config.has_section(SECTION_FILE):
            config.add_section(SECTION_FILE)

        if self.notebookType == 1:
            config.set(SECTION_FILE, TMPPATH_NAME, "\n".join(self.full_paths))

        if self.notebookType == 2:
            config.set(SECTION_FILE, IMAGEPATH_NAME,
                       "\n".join(self.full_paths))

        config[SECTION_PATH] = {
            PAL_NAME: self.path_pal,
            FLODER_NAME: self.path_floder,
            TEMPLATE_NAME: self.path_template
        }

        config[SECTION_SETTING] = {
            THEATER_NAME: ",".join(self.theaters),
            AUTOPAL_NAME: self.var_auto_pal.get()
        }

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    def isfile(self, some_path):
        if Path(some_path).is_file():
            return some_path
        return ''

    def load_config(self):

        # 读取 config
        SECTION_FILE = 'Files'
        TMPPATH_NAME = 'TmpPath'
        IMAGEPATH_NAME = 'ImagePath'

        SECTION_PATH = 'Paths'
        PAL_NAME = 'Palette'
        FLODER_NAME = 'FileFloder'
        TEMPLATE_NAME = 'Template'

        SECTION_SETTING = 'Settings'
        AUTOPAL_NAME = 'AutoPal'
        THEATER_NAME = 'Theater'

        if not os.path.exists(CONFIG_PATH):
            return

        config = configparser.ConfigParser()
        config.read(CONFIG_PATH, encoding="utf-8")

        # 气候列表
        t_basic = config.get(SECTION_SETTING, THEATER_NAME,
                             fallback=".tem,.urb,.sno,.ubn,.des,.lun")
        if not t_basic:  # 防止空值，不能只用 fallback
            self.theaters = ['.tem', '.urb', '.sno', '.ubn', '.des', '.lun']
        else:
            self.theaters = t_basic.split(',')

        # 自动色盘
        auto_pal = config.get(SECTION_SETTING, AUTOPAL_NAME,
                              fallback=True)
        if auto_pal in {'enable', 'disable'}:
            self.var_auto_pal.set(auto_pal)
        else:
            self.var_auto_pal.set('enable')

        # 刷新文件列表
        if self.notebookType == 1:
            PATH_NAME = TMPPATH_NAME
        if self.notebookType == 2:
            PATH_NAME = IMAGEPATH_NAME

        raw = config.get(SECTION_FILE, PATH_NAME, fallback="")
        self.lst_files = [i for i in raw.splitlines(
        ) if i.strip() and Path(i).is_file()]
        self.lb_files.delete(0, tk.END)
        self.full_paths.clear()
        for f in self.lst_files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, os.path.basename(f))

        # 刷新路径列表
        # 1) 刷新文件夹列表
        self.path_floder = config.get(SECTION_PATH, FLODER_NAME, fallback="")
        self.lb_floder.delete(0, tk.END)
        self.lb_floder.insert(tk.END, self.path_floder)

        # 2) 刷新色盘列表
        self.path_pal = self.isfile(config.get(
            SECTION_PATH, PAL_NAME, fallback=""))
        self.lb_pal.delete(0, tk.END)
        self.lb_pal.insert(tk.END, self.path_pal)

        # 2) 刷新色盘列表
        self.path_template = self.isfile(config.get(
            SECTION_PATH, TEMPLATE_NAME, fallback=""))
        self.lb_template.delete(0, tk.END)
        self.lb_template.insert(tk.END, self.path_template)

    # --------- 图像 ---------

    # def show_preview(self):
    #     if self.preview_img is None:
    #         return

    #     tk_img = ImageTk.PhotoImage(self.preview_img)
    #     self.preview_label.configure(image=tk_img)
    #     self.preview_label.image = tk_img  # 强引用

# ----------- 导出图像 -----------


class Tab_One(FilesTab):
    def _init_ui(self):
        super()._init_ui()

        self.notebookType = 1
        # ----- 文件夹选择

        self.lb_template.place_forget()
        self.btn_template.place_forget()

        # ----- 选项设置

        # 按钮区
        ttk.Button(self.btn_frame, text='添加',
                   command=self.btn_add_files).place(x=3, y=0, width=80, height=25)
        ttk.Button(self.btn_frame, text='移除',
                   command=self.btn_remove_selected).place(x=3, y=30, width=80, height=25)
        ttk.Button(self.btn_frame, text='清空全部',
                   command=self.btn_remove_all).place(x=3, y=60, width=80, height=25)
        ttk.Button(self.btn_frame, text='导出',
                   command=self.btn_run).place(x=3, y=110, width=80, height=25)

        self.ckb_frame.place(x=300, y=90, width=400, height=300)

        self.var_exp_png = tk.StringVar(value='enable')

        self.ckb_exp_png = ttk.Checkbutton(
            self.ckb_frame, text='导出 PNG', variable=self.var_exp_png, onvalue='enable', offvalue='disable')

        self.ckb_exp_png.place(x=0, y=25, width=80, height=25)
        ToolTip(self.ckb_exp_png, "导出为 PNG 文件")

        self.var_exp_bmp = tk.StringVar(value='disable')

        self.ckb_exp_bmp = ttk.Checkbutton(
            self.ckb_frame, text='导出 BMP', variable=self.var_exp_bmp, onvalue='enable', offvalue='disable')

        self.ckb_exp_bmp.place(x=0, y=50, width=80, height=25)
        ToolTip(self.ckb_exp_bmp, "导出为 BMP 文件")

        ToolTip(self.text_save_name, "导出文件命名为[此处输入文本][01起始的序号].[png/bmp]")

    # --------- 导出图像 ---------

    def btn_run(self):
        bmp = self.var_exp_bmp.get() == 'enable'
        png = self.var_exp_png.get() == 'enable'
        if not (bmp or png):
            messagebox.showwarning('警告', '未选择导出格式')
            return
        if not Path(self.path_pal).is_file():
            messagebox.showwarning('警告', '未选择色盘')
            return

        prefix = self.text_prefix.get("1.0", tk.END).split('\n')[0]
        suffix = self.text_suffix.get("1.0", tk.END).split('\n')[0]

        self.lst_files = self.full_paths.copy()
        # 选取的文件
        render_files = [
            str(Path(p))    # 斜杠方向
            for p in self.lst_files
            if Path(p).is_file() and
            Path(p).name.startswith(prefix) and
            Path(p).name.endswith(suffix)
        ]

        # 批处理文件夹
        if not suffix:
            suffix = tuple(self.theaters.copy())
        if not self.path_floder == '' and Path(self.path_floder).is_dir():
            floder_files = [
                str(p)
                for p in Path(self.path_floder).iterdir()
                if p.is_file() and
                (str(p) not in render_files) and
                p.name.startswith(prefix) and
                p.name.endswith(suffix)
            ]
            render_files += floder_files
        if not render_files:
            messagebox.showwarning('警告', '未选择需要导出的 TMP 文件')
            return

        self.log(f'开始导出已选择的 {len(render_files)} 个文件')
        self.save_config()
        self.load_config()

        # 调用
        save_index = 1
        for i, file in enumerate(render_files):

            # 色盘
            palette = self.get_palette(file_name=file)
            print(palette)
            self.log(f'正在导出第{i+1}个文件 {file}')

            text_save_name = self.text_save_name.get(
                "1.0", tk.END).split('\n')[0]

            if not text_save_name == '':
                export_img = str(Path(file).parent / text_save_name) + \
                    str(save_index).zfill(len(render_files))
                save_index += 1
            else:
                export_img = file[:-4]

            tmp = TmpFile(file)

            render.render_full_png(
                tmp, palette, export_img,
                render_extra=True,
                background_index=0, out_bmp=bmp, out_png=png)

        self.log(f'已导出全部文件')

# ----------- 导入图像 -----------


class Tab_Two(FilesTab):
    def _init_ui(self):
        super()._init_ui()

        self.notebookType = 2

        # 按钮区

        ttk.Button(self.btn_frame, text='添加',
                   command=self.btn_add_files).place(x=3, y=0, width=80, height=25)
        ttk.Button(self.btn_frame, text='移除',
                   command=self.btn_remove_selected).place(x=3, y=30, width=80, height=25)
        ttk.Button(self.btn_frame, text='清空全部',
                   command=self.btn_remove_all).place(x=3, y=60, width=80, height=25)
        ttk.Button(self.btn_frame, text='导入',
                   command=self.btn_run).place(x=3, y=110, width=80, height=25)

        # 导出设置
        self.lb_save_name.place(x=100)
        self.text_save_name.place(x=158)

        self.lb_prefix.place(x=100)
        self.text_prefix.place(x=135)

        self.lb_suffix.place(x=100)
        self.text_suffix.place(x=135)

        self.ckb_frame.place(x=270, y=110, width=400, height=300)

        self.var_auto_radar = tk.StringVar(value='enable')
        self.var_impt_img = tk.StringVar(value='enable')
        self.var_impt_ext = tk.StringVar(value='enable')

        self.ckb_auto_radar = ttk.Checkbutton(
            self.ckb_frame, text='自动雷达色', variable=self.var_auto_radar, onvalue='enable', offvalue='disable')
        self.ckb_auto_radar.place(x=0, y=25, width=100, height=25)
        ToolTip(self.ckb_auto_radar, "雷达色")

        self.ckb_impt_img = ttk.Checkbutton(
            self.ckb_frame, text='导入图像', variable=self.var_impt_img, onvalue='enable', offvalue='disable')
        self.ckb_impt_img.place(x=0, y=50, width=100, height=25)
        ToolTip(self.ckb_impt_img, "导入图像")

        self.ckb_impt_ext = ttk.Checkbutton(
            self.ckb_frame, text='导入 Extra', variable=self.var_impt_ext, onvalue='enable', offvalue='disable')
        self.ckb_impt_ext.place(x=0, y=75, width=100, height=25)
        ToolTip(self.ckb_impt_ext, "导入 Extra")

        # 指定模板
        self.var_specify_template = tk.StringVar()
        self.cb_specify_template = ttk.Combobox(
            self.ckb_frame,
            textvariable=self.var_specify_template,
            values=("使用选中模板", "图像文件名匹配", "模板文件夹匹配"),
            state="readonly")
        ToolTip(self.cb_specify_template,
                "使用选中模板：按当前预览模板导出全部文件\n"
                "图像文件名匹配：在图像所在文件夹中选择图像同名文件\n"
                "模板文件夹匹配：在当前选中模板所在文件夹中选择图像同名文件\n"
                "匹配时默认自动色盘转换全部气候")
        ttk.Label(self.ckb_frame, text='导入模式：').place(
            x=260, y=0, width=60, height=20)
        self.cb_specify_template.place(x=260, y=25, width=115, height=24)
        self.cb_specify_template.current(0)

        # 模板
        self.path_frame.place(height=85)

        ToolTip(self.text_save_name,
                "导出文件命名为[此处输入文本][01起始的序号].[气候名]\n对于导出地形，超过99后需要后续处理")
    # --------- 行为逻辑 ---------

    def btn_add_files(self):
        files = filedialog.askopenfilenames(title='选择文件',    filetypes=[
            ("Image files", "*.png *.bmp"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp")
        ])
        for f in files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, os.path.basename(f))
        self.save_config()

    def file_on_select(self, event):
        if not self.lb_files.curselection():
            return

        index = self.lb_files.curselection()[0]
        file = self.full_paths[index]
        print(file)
        render_img = Image.open(file).convert(
            "RGBA")  # self.render_preview(file)
        self.show_preview(render_img)

    # # 图片预览
    # def render_preview(self, file):
    #     export_img = file[:-4] + '.png'

    #     palette = self.get_palette(file_name=file)

    #     tmp = TmpFile(file)
    #     render_img = render.render_full_png(
    #         tmp, palette, export_img,
    #         render_extra=True,
    #         background_index=0, out_bmp=False, out_png=False)
    #     return render_img

    def show_preview(self, render_img,palette=None):

        # 填充边框颜色
        border_color1 = (255, 255, 255, 255) if render_img.mode == 'RGBA' else (
            255, 255, 255)
        border_color2 = (225, 225, 225, 255) if render_img.mode == 'RGBA' else (
            225, 225, 225)

        p_width = self.image_label_width - 8
        p_height = self.image_label_height - 8

        if not palette == None:
            render_img = render_img.copy()
            pixels = render_img.load()

            old_color = palette[0]
            new_color = border_color1

            for x in range(render_img.width):
                for y in range(render_img.height):
                    if pixels[x, y] == old_color:
                        pixels[x, y] = new_color


        temp_img = Image.new(
            render_img.mode, (p_width + 2, p_height + 2), border_color1)

        w1, h1 = temp_img.size
        w2, h2 = render_img.size
        pos = (int(0.5*(w1-w2)), int(0.5*(h1-h2)))

        if render_img.mode == "RGBA":
            temp_img.paste(render_img, pos, render_img)
        else:
            temp_img.paste(render_img, pos)

        preview_img = Image.new(
            render_img.mode, (p_width + 4, p_height + 4), border_color2)
        preview_img.paste(temp_img, (1, 1))

        # 根据预览大小缩放
        width, height = preview_img.size

        w = max(1, self.image_label.winfo_width())
        h = max(1, self.image_label.winfo_height())

        if width < w or height < h:
            preview_img = preview_img.resize((w, h), Image.LANCZOS)

        self.current_image = ImageTk.PhotoImage(preview_img)
        self.image_label.config(image=self.current_image)

    # --------- 导出图像 ---------

    def btn_run(self):
        
        SAVE_ADDITION = ''

        if not Path(self.path_pal).is_file():
            messagebox.showwarning('警告', '未选择色盘')
            return

        prefix = self.text_prefix.get("1.0", tk.END).split('\n')[0]
        suffix = self.text_suffix.get("1.0", tk.END).split('\n')[0]

        self.lst_files = self.full_paths.copy()
        # 选取的文件
        render_files = [
            str(Path(p))    # 斜杠方向
            for p in self.lst_files
            if Path(p).is_file() and
            Path(p).name.startswith(prefix) and
            Path(p).name.endswith(suffix)
        ]

        # 批处理文件夹
        if not suffix:
            suffix = tuple(['.png', '.bmp'])
        if not self.path_floder == '' and Path(self.path_floder).is_dir():

            floder_files = [
                str(p)
                for p in Path(self.path_floder).iterdir()
                if p.is_file() and
                (str(p) not in render_files) and
                p.name.startswith(prefix) and
                p.name.endswith(suffix)
            ]
            render_files += floder_files
        if not render_files:
            messagebox.showwarning('Warning', 'Not file choosed')
            return

        self.log(f'开始导出已选择的{len(render_files)}个文件')
        self.save_config()
        self.load_config()

        # 模板
        temp_mode = self.var_specify_template.get() == "使用选中模板"
        search_img_mode = self.var_specify_template.get() == "图像文件名匹配"
        search_tem_mode = self.var_specify_template.get() == "模板文件夹匹配"

        if temp_mode:
            self.log(f'使用选中模板导出')

        if search_img_mode:
            self.log(f'使用图像文件夹导出')

        if search_tem_mode:
            self.log(f'使用模板文件夹导出')

        if not (search_img_mode or temp_mode or search_tem_mode):
            messagebox.showwarning('警告', '未选择导出格式')
            return

        # 调用

        save_index = 1
        for i, img_file in enumerate(render_files):

            import_img = img_file
            img_file_name = Path(import_img).name
            import_template = self.path_template
            temp_file_name = Path(import_template).name

            img_floder = Path(import_img).parent
            tem_floder = Path(import_template).parent

            text_save_name = self.text_save_name.get(
                "1.0", tk.END).split('\n')[0]

            # 色盘

            self.log(f'正在导出第{i+1}个文件 {import_img}')
            # 模板
            if temp_mode:
                # print("使用选中模板")
                template_tmp = import_template
                palette = self.get_palette(file_name=temp_file_name)

                tmp = TmpFile(template_tmp)

                print(f'template_tmp{template_tmp}import_img{import_img}')
                impt.import_image_to_tmp(
                    tmp, import_img, palette, background_index=0,
                    auto_radar=self.var_auto_radar.get() == 'enable',
                    change_normal=self.var_impt_img.get() == 'enable',
                    change_extra=self.var_impt_ext.get() == 'enable')

                if not text_save_name == '':
                    import_save = str(img_floder / text_save_name) + \
                        str(save_index).zfill(2) + template_tmp[-4:]
                    save_index += 1
                    print(import_save)
                else:
                    import_save = import_img[:-4] + SAVE_ADDITION + template_tmp[-4:]
                impt.save_tmpfile(tmp, import_save)
                continue

            if search_img_mode:
                find_any = False
                for t in self.theaters:
                    if Path(import_img[:-4] + t).is_file():
                        find_any = True

                        pal_name = 'iso' + t[1:] + '.pal'
                        pal_floder = Path(self.path_pal).parent
                        pal_file = pal_floder / pal_name
                        palette = PalFile(pal_file).palette

                        template_tmp = import_img[:-4] + t

                        tmp = TmpFile(template_tmp)
                        impt.import_image_to_tmp(
                            tmp, import_img, palette, background_index=0,
                            auto_radar=self.var_auto_radar.get() == 'enable',
                            change_normal=self.var_impt_img.get() == 'enable',
                            change_extra=self.var_impt_ext.get() == 'enable')

                        if not text_save_name == '':
                            import_save = str(
                                img_floder / text_save_name) + str(save_index).zfill(2) + t
                            save_index += 1
                        else:
                            import_save = import_img[:-4] + SAVE_ADDITION + t
                        impt.save_tmpfile(tmp, import_save)

                if not find_any:
                    self.log(f'警告 - 文件 {import_img}\n未找到对应模板')
                continue

            if search_tem_mode:
                find_any = False
                for t in self.theaters:

                    if Path(str(tem_floder / img_file_name[:-4]) + t).is_file():
                        find_any = True

                        pal_name = 'iso' + t[1:] + '.pal'
                        pal_floder = Path(self.path_pal).parent
                        pal_file = pal_floder / pal_name
                        palette = PalFile(pal_file).palette

                        template_tmp = str(tem_floder / img_file_name[:-4]) + t

                        tmp = TmpFile(template_tmp)
                        impt.import_image_to_tmp(
                            tmp, import_img, palette, background_index=0,
                            auto_radar=self.var_auto_radar.get() == 'enable',
                            change_normal=self.var_impt_img.get() == 'enable',
                            change_extra=self.var_impt_ext.get() == 'enable')

                        if not text_save_name == '':
                            import_save = str(
                                img_floder / text_save_name) + str(save_index).zfill(2) + t
                            save_index += 1
                        else:
                            import_save = import_img[:-4] + SAVE_ADDITION + t
                        impt.save_tmpfile(tmp, import_save)
                if not find_any:
                    self.log(f'警告 - 文件 {import_img}\n未找到对应模板')
                continue

        self.log(f'已导出全部文件')


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('神秘东西')
        self.geometry('700x620')

        notebook = ttk.Notebook(self)
        notebook.place(x=10, y=10, width=680, height=600)

        # 第一标签页
        self.tab_files = Tab_One(notebook, self.append_log)
        notebook.add(self.tab_files, text='导出图像')

        # 第二标签页
        self.tab_state = Tab_Two(notebook, self.append_log)
        notebook.add(self.tab_state, text='导入图像')

        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self._init_log()

    def _init_log(self):
        log_frame = ttk.Frame(self)
        log_frame.place(x=20, y=450, width=660, height=150)

        ttk.Label(log_frame, text='Log:', relief='flat').pack(anchor=tk.W)

        self.txt_log = tk.Text(log_frame, height=6,
                               state=tk.DISABLED, wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    def append_log(self, msg):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, msg + '\n')
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def on_tab_changed(self, event):
        notebook = event.widget
        current_frame = notebook.nametowidget(notebook.select())

        if hasattr(current_frame, "load_config"):
            current_frame.load_config()


if __name__ == '__main__':
    app = App()
    app.mainloop()
