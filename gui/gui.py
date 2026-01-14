import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import configparser

from logic.modules import TmpFile, PalFile
# import logic.image as impt
import logic.render as render

from pathlib import Path
import sys
import traceback


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

SECTION_LIST = "Files"
DIR_TMP = "TMP_Files"
DIR_IMAGE = "Image_Files"
DIR_TMP_CONVERT = "TMP_Convert_Files"

SECTION_PATH = "Paths"
DIR_PAL_SOURCE = "Source_Palette"
DIR_PAL_TARGET = "Target_Palette"
DIR_EXPORT = "Export_Dir"
DIR_TEMPLATE = "Template_TMP"

SECTION_SETTING = "Options"
SET_PAL_SOURCE = "Auto_Match_Source_Palette"
SET_PAL_TARGET = "Auto_Match_Target_Palette"
SET_THEATER = "Theater"

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
        self.path_out_floder = ""
        self.path_pal_source = ""
        self.path_pal_target = ""
        self.path_template = ""

        self.current_image = None  # 保存 PhotoImage 引用

        self.only_start = ""
        self.only_end = ""

        self.image_label_width = 408
        self.image_label_height = 208
        self.theaters = [".tem", ".urb", ".sno", ".ubn", ".des", ".lun"]
        self._init_ui()

        self.load_config()
        self.tmp_suffix = "*"+" *".join(self.theaters)

    def log(self, msg, level="INFO"):
        self.log_callback(msg, level)

    def safe_call(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            self.log(traceback.format_exc(), "ERROR")
            return None
    # --------- UI ---------

    def _init_ui(self):
        self.lb_show_type = "PAGE_0"
        # ----- 文件列表
        list_frame = ttk.Frame(self)
        list_frame.place(x=10, y=10, width=250, height=370)

        self.lb_files = tk.Listbox(
            list_frame, selectmode=tk.EXTENDED, relief="flat", takefocus=False)
        self.lb_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                           command=self.lb_files.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.lb_files.config(yscrollcommand=sb.set)

        # ----- 文件夹选择
        self.path_frame = ttk.Frame(self)
        self.path_frame.place(x=260, y=10, width=500, height=80)

        # 1) 批处理路径选择
        self.ent_out_floder = tk.Entry(
            self.path_frame, relief="flat", insertwidth=1)
        self.ent_out_floder.place(x=0, y=0, width=400, height=25)

        ttk.Button(
            self.path_frame, text="导出目录", command=self.btn_choose_folder
        ).place(x=420, y=0, width=80, height=25)

        # 2) 色盘选择
        self.ent_pal_source = tk.Entry(
            self.path_frame, relief="flat", insertwidth=1)
        self.ent_pal_source.place(x=0, y=30, width=400, height=25)

        self.btn_pal_source = ttk.Button(
            self.path_frame, text="选择色盘", command=self.btn_choose_pal_input
        )
        self.btn_pal_source.place(x=420, y=30, width=80, height=25)

        # 气候转换双色盘
        self.ent_pal_target = tk.Entry(
            self.path_frame, relief="flat", insertwidth=1)
        self.ent_pal_target.place(x=0, y=60, width=400, height=25)

        self.btn_pal_target = ttk.Button(
            self.path_frame, text="选择色盘", command=self.btn_choose_pal_output
        )
        self.btn_pal_target.place(x=420, y=60, width=80, height=25)

        # 3) 模板选择
        self.ent_template = tk.Entry(
            self.path_frame, relief="flat", insertwidth=1)
        self.ent_template.place(x=0, y=60, width=400, height=25)

        self.btn_template = ttk.Button(
            self.path_frame, text="选择模板", command=self.btn_choose_template
        )
        self.btn_template.place(x=420, y=60, width=80, height=25)

        # ----- 选项设置
        self.ckb_frame = ttk.Frame(self)

        # 1) Checkbox 自动色盘
        self.var_auto_pal_source = tk.StringVar(value="enable")

        self.ckb_auto_pal_source = ttk.Checkbutton(
            self.ckb_frame, text="自动色盘", variable=self.var_auto_pal_source, onvalue="enable", offvalue="disable")

        self.ckb_auto_pal_source.place(x=0, y=0, width=80, height=25)

        self.var_auto_pal_target = tk.StringVar(value="enable")
        self.ckb_auto_pal_target = ttk.Checkbutton(
            self.ckb_frame, text="导出地形", variable=self.var_auto_pal_target, onvalue="enable", offvalue="disable")

        self.ckb_auto_pal_target.place(x=0, y=50, width=80, height=25)

        # 2) Label 前缀
        self.lb_prefix = ttk.Label(self.ckb_frame, text="限定前缀：")
        self.lb_prefix.place(x=170, y=0, width=80, height=25)

        self.ent_prefix = tk.Entry(
            self.ckb_frame, relief="flat", insertwidth=1)
        self.ent_prefix.place(x=230, y=2, width=104, height=20)
        ToolTip(self.ent_prefix, "只转换带有该前缀的文件")

        # 3) Label 后缀
        self.lb_suffix = ttk.Label(self.ckb_frame, text="限定后缀：")
        self.lb_suffix.place(x=170, y=28, width=80, height=25)

        self.ent_suffix = tk.Entry(
            self.ckb_frame, relief="flat", insertwidth=1)
        self.ent_suffix.place(x=230, y=30, width=104, height=20)
        ToolTip(self.ent_suffix, "只转换带有该后缀的文件，包含文件后缀名")
        # \n符合该后缀的文件将跳过气候检查

        # 4) Label 导出名称
        self.lb_save_name = ttk.Label(self.ckb_frame, text="导出名称：")
        self.lb_save_name.place(x=170, y=58, width=80, height=25)

        self.ent_save_name = tk.Entry(
            self.ckb_frame, relief="flat", insertwidth=1)
        self.ent_save_name.place(x=230, y=60, width=104, height=20)

        # 按钮区
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.place(x=265, y=270, width=420, height=250)

        # 右侧预览区
        self.image_label = ttk.Label(self, anchor="center", relief="flat")
        self.image_label.place(
            x=365, y=200, width=self.image_label_width, height=self.image_label_height)

        self.lb_files.bind("<<ListboxSelect>>", self.file_on_select)
        self.show_preview(Image.new("RGB", (10, 10), (255, 255, 255)))

    # --------- 行为逻辑 ---------

    def get_source_pal(self, file):
        '''
        返回 PalFile.palette 作为色盘

        :file: 选择 file 末端三字符作为气候名
        '''

        if self.var_auto_pal_source.get() != "enable":
            return PalFile(self.path_pal_source).palette

        pal_name = f"iso{file[-3:]}.pal"
        pal_file = Path(self.path_pal_source).parent / pal_name

        if pal_file.is_file():
            return PalFile(pal_file).palette

        self.log(f"未找到色盘{pal_file}\n使用选中色盘", "WARN")
        return PalFile(self.path_pal_source).palette

    def get_target_pal(self, file):
        '''
        返回 PalFile.palette 作为色盘

        :file: 选择 file 末端三字符作为气候名
        '''
        if self.var_auto_pal_target.get() != "enable":
            return PalFile(self.path_pal_target).palette

        pal_name = f"iso{file[1:]}.pal"
        pal_file = Path(self.path_pal_target).parent / pal_name

        if pal_file.is_file():
            return PalFile(pal_file).palette

        self.log(f"未找到色盘{pal_file}\n使用选中色盘", "WARN")
        return PalFile(self.path_pal_target).palette

    def get_int(self, str):
        if str == "":
            return 1
        try:
            num = int(str)
            if num >= 0:
                return num
        except ValueError:
            return None
        return None

    def get_output_text_name(self):
        '''
        获取导出名称，返回 text, start_index

        :text: 命名文本
        :start_index: 起始序号
        '''
        raw_text = self.ent_save_name.get().split("\n", 1)[0]
    
        if not raw_text:
            return "", 1

        at_count = raw_text.count("@")

        if at_count == 0:
            return raw_text, 1

        if at_count > 1:
            self.log("导出名称存在多个@，使用原名称\n导出名称格式应为 [文本@起始序号] 或 [文本]，只能包含 0 或 1 个 @","WARN")
            return raw_text, 1

        text, index_str = raw_text.split("@")

        start_index = self.get_int(index_str)

        if not text or start_index is None:
            self.log("导出名称中 [文本] 为空 或 [起始序号] 错误，使用原名称\n""导出名称格式应为 [文本@起始序号] 或 [文本]","WARN")
            return raw_text, 1
        return text, start_index

    def btn_choose_folder(self):
        floder = filedialog.askdirectory(title="选择导出文件夹")
        if not floder:
            self.path_out_floder = ""
            self.ent_out_floder.delete(0, tk.END)
            self.save_config()
            return

        self.path_out_floder = floder
        self.ent_out_floder.delete(0, tk.END)
        self.ent_out_floder.insert(tk.END, str(floder))
        self.save_config()

    def btn_choose_pal_input(self):

        while True:
            pal = filedialog.askopenfilename(
                title="选择 pal 文件",    filetypes=[("PAL files", "*.pal")])
            if not pal:
                self.path_pal_source = ""
                self.ent_pal_source.delete(0, tk.END)
                self.save_config()
                return
            if pal.endswith(".pal"):
                self.path_pal_source = pal
                self.ent_pal_source.delete(0, tk.END)
                self.ent_pal_source.insert(0, pal)
                self.save_config()
                return
            messagebox.showwarning("Warning", "Not a pal")

    def btn_choose_pal_output(self):

        while True:
            pal = filedialog.askopenfilename(
                title="选择 pal 文件",    filetypes=[("PAL files", "*.pal")])
            if not pal:
                self.path_pal_target = ""
                self.ent_pal_target.delete(0, tk.END)
                self.save_config()
                return
            if pal.endswith(".pal"):
                self.path_pal_target = pal
                self.ent_pal_target.delete(0, tk.END)
                self.ent_pal_target.insert(0, pal)
                self.save_config()
                return
            messagebox.showwarning("Warning", "Not a pal")

    def btn_choose_template(self):
        template = filedialog.askopenfilename(title="选择文件",    filetypes=[
            ("TMP files", self.tmp_suffix)])
        if not template:
            self.path_template = ""
            self.ent_template.delete(0, tk.END)
            self.save_config()
            return
        else:
            self.path_template = template
            self.ent_template.delete(0, tk.END)
            self.ent_template.insert(0, template)
            self.save_config()
            return

    def btn_add_files(self):
        files = filedialog.askopenfilenames(title="选择文件",    filetypes=[
            ("TMP files", self.tmp_suffix)])
        for f in files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, Path(f).name)
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

        if self.lb_show_type == "PAGE_1" or self.lb_show_type == "PAGE_3":
            self.path_pal_source = self.ent_pal_source.get()

            if not Path(self.path_pal_source).is_file():
                return
            index = self.lb_files.curselection()[0]
            file = self.full_paths[index]

            render_img, palette = self.render_preview(file)
            self.show_preview(render_img, palette)

        elif self.lb_show_type == "PAGE_2":
            index = self.lb_files.curselection()[0]
            file = self.full_paths[index]

            render_img = Image.open(file).convert(
                "RGBA")  # self.render_preview(file)
            self.show_preview(render_img)

    # 图片预览
    def render_preview(self, file):
        export_img = file[:-4] + ".png"

        tmp = TmpFile(file)

        if hasattr(self, 'var_zdata_mode') and self.var_zdata_mode is not None:
            if self.var_zdata_mode.get() == "enable":
                render_img = render.render_full_ZData(tmp, export_img)
                return render_img, None

        if self.var_auto_pal_source.get() == "enable":
            pal_name = "iso" + file[-3:] + ".pal"

            print(pal_name)
            self.path_pal_source = self.ent_pal_source.get()
            pal_floder = Path(self.path_pal_source).parent
            pal_file = pal_floder / pal_name

            if Path(pal_file).is_file():
                palette = PalFile(pal_file).palette
            else:
                self.log(f"未找到色盘{pal_file}\n使用选中色盘", "WARN")
                palette = PalFile(self.path_pal_source).palette
        else:
            palette = PalFile(self.path_pal_source).palette

        render_img = render.render_full_png(
            tmp, palette, export_img,
            render_extra=True, out_bmp=False, out_png=False)

        return render_img, palette

    def show_preview(self, render_img, palette=None):

        # 填充边框颜色
        border_color1 = (255, 255, 255, 255) if render_img.mode == "RGBA" else (
            255, 255, 255)
        border_color2 = (225, 225, 225, 255) if render_img.mode == "RGBA" else (
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

        # 根据预览大小缩放
        max_w = self.image_label_width - 4
        max_h = self.image_label_height - 4

        width, height = render_img.size
        if width > max_w:
            render_img = render_img.resize(
                (max_w, max(int(height * max_w / width), 1)), Image.LANCZOS)

        width, height = render_img.size
        if height > max_h:
            render_img = render_img.resize(
                (max(int(width * max_h / height), 1), max_h), Image.LANCZOS)

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

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config.optionxform = str

        if Path(CONFIG_PATH).is_file():
            config.read(CONFIG_PATH, encoding="utf-8")

            self.path_pal_source = str(Path(self.ent_pal_source.get()))
            self.path_pal_target = str(Path(self.ent_pal_target.get()))
            self.path_out_floder = str(Path(self.ent_out_floder.get()))
            self.path_template = str(Path(self.ent_template.get()))

        if not config.has_section(SECTION_LIST):
            config.add_section(SECTION_LIST)

        if self.lb_show_type == "PAGE_1":
            config.set(SECTION_LIST, DIR_TMP,
                       "\n".join(self.full_paths))

        if self.lb_show_type == "PAGE_2":
            config.set(SECTION_LIST, DIR_IMAGE,
                       "\n".join(self.full_paths))

        if self.lb_show_type == "PAGE_3":
            config.set(SECTION_LIST, DIR_TMP_CONVERT,
                       "\n".join(self.full_paths))

        config[SECTION_PATH] = {
            DIR_PAL_SOURCE: self.path_pal_source,
            DIR_PAL_TARGET: self.path_pal_target,
            DIR_EXPORT: self.path_out_floder,
            DIR_TEMPLATE: self.path_template
        }

        config[SECTION_SETTING] = {
            SET_THEATER: ",".join(self.theaters),
            SET_PAL_SOURCE: self.var_auto_pal_source.get(),
            SET_PAL_TARGET: self.var_auto_pal_target.get()
        }

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    def isfile(self, some_path):
        if Path(some_path).is_file():
            return str(Path(some_path))
        return ""

    def load_config(self):

        # 读取 config

        if not Path(CONFIG_PATH).exists():
            self.save_config()
            return

        config = configparser.ConfigParser()
        config.read(CONFIG_PATH, encoding="utf-8")

        # 气候列表
        t_basic = config.get(SECTION_SETTING, SET_THEATER,
                             fallback=".tem,.urb,.sno,.ubn,.des,.lun")
        if not t_basic:  # 防止空值，不能只用 fallback
            self.theaters = [".tem", ".urb", ".sno", ".ubn", ".des", ".lun"]
        else:
            self.theaters = t_basic.split(",")

        # 自动色盘
        auto_pal = config.get(SECTION_SETTING, SET_PAL_SOURCE,
                              fallback=True)
        if auto_pal in {"enable", "disable"}:
            self.var_auto_pal_source.set(auto_pal)
        else:
            self.var_auto_pal_source.set("enable")

        auto_pal2 = config.get(SECTION_SETTING, SET_PAL_TARGET,
                               fallback=True)
        if auto_pal2 in {"enable", "disable"}:
            self.var_auto_pal_target.set(auto_pal2)
        else:
            self.var_auto_pal_target.set("enable")

        # 刷新文件列表
        if self.lb_show_type == "PAGE_1":
            list_name = DIR_TMP
        if self.lb_show_type == "PAGE_2":
            list_name = DIR_IMAGE
        if self.lb_show_type == "PAGE_3":
            list_name = DIR_TMP_CONVERT

        raw = config.get(SECTION_LIST, list_name, fallback="")
        self.lst_files = [i for i in raw.splitlines(
        ) if i.strip() and Path(i).is_file()]
        self.lb_files.delete(0, tk.END)
        self.full_paths.clear()
        for f in self.lst_files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, Path(f).name)

        # 刷新路径列表
        # 1) 刷新文件夹列表
        self.path_out_floder = str(Path(config.get(
            SECTION_PATH, DIR_EXPORT, fallback="")))
        if self.path_out_floder == ".":  # 目录为空特殊处理
            self.path_out_floder = ""
        self.ent_out_floder.delete(0, tk.END)
        self.ent_out_floder.insert(tk.END, self.path_out_floder)

        # 2) 刷新色盘列表
        self.path_pal_source = self.isfile(config.get(
            SECTION_PATH, DIR_PAL_SOURCE, fallback=""))
        self.ent_pal_source.delete(0, tk.END)
        self.ent_pal_source.insert(0, self.path_pal_source)

        self.path_pal_target = self.isfile(config.get(
            SECTION_PATH, DIR_PAL_TARGET, fallback=""))
        self.ent_pal_target.delete(0, tk.END)
        self.ent_pal_target.insert(0, self.path_pal_target)

        # 2) 刷新色盘列表
        self.path_template = self.isfile(config.get(
            SECTION_PATH, DIR_TEMPLATE, fallback=""))
        self.ent_template.delete(0, tk.END)
        self.ent_template.insert(0, self.path_template)
