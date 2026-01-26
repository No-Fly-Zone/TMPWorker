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
SETTING_PATH = Path(CONFIG_DIR) / CONFIG_FILE

PRESET_FILE = "export_config.ini"
PRESET_PATH = Path(CONFIG_DIR) / PRESET_FILE

SECTION_EXP_NAME = "Names"
SECTION_EXP_PRESET = "Presets"

SECTION_LIST = "Files"
DIR_TMP = "TMP_Files"
DIR_IMAGE = "Image_Files"
DIR_TMP_CONVERT = "TMP_Convert_Files"
DIR_ZDATA = "ZData_Files"

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


class AdvancedSortableTreeview(ttk.Treeview):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        # 绑定事件
        self.bind('<ButtonPress-1>', self.on_press)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)

        # 拖拽相关变量
        self.drag_data = {
            'x': 0, 'y': 0,
            'item': None,
            'values': None,
            'text': None
        }
        self.drag_window = None

    def on_press(self, event):
        """鼠标按下时记录拖拽开始"""
        item = self.identify_row(event.y)
        if item:
            self.drag_data['item'] = item
            self.drag_data['x'] = event.x
            self.drag_data['y'] = event.y
            self.drag_data['values'] = self.item(item, 'values')
            self.drag_data['text'] = self.item(item, 'text')

    def on_drag(self, event):
        """拖拽过程中显示预览窗口"""
        if not self.drag_data['item']:
            return

        # 创建拖拽预览窗口
        if not self.drag_window:
            self.drag_window = tk.Toplevel(self)
            self.drag_window.overrideredirect(True)
            self.drag_window.attributes('-alpha', 0.7)

            # 创建预览内容
            frame = tk.Frame(self.drag_window, bg='lightblue', relief='solid')
            frame.pack(fill=tk.BOTH, expand=True)

            # 显示项目内容
            text = self.drag_data['text']
            values = self.drag_data['values']

            tk.Label(frame, text=text, bg='lightblue',
                     font=('Arial', 10, 'bold')).pack(pady=2, padx=10)

            if values:
                for value in values:
                    tk.Label(frame, text=value, bg='lightblue').pack(
                        pady=1, padx=10)

        # 移动预览窗口
        self.drag_window.geometry(f'+{event.x_root}+{event.y_root}')

        # 显示插入位置指示线
        self.show_insert_position(event.y)

    def show_insert_position(self, y):
        """显示插入位置指示线"""
        # 移除旧的指示线
        for item in self.get_children():
            tags = self.item(item, 'tags')
            if tags and 'insert_pos' in tags:
                self.item(item, tags=())

        # 找到目标位置
        target_item = self.identify_row(y)
        if target_item:
            # 高亮显示目标位置
            self.item(target_item, tags=('insert_pos',))
            self.tag_configure('insert_pos', background='lightyellow')

    def on_release(self, event):
        """释放鼠标时执行排序"""
        if self.drag_data['item']:
            target_item = self.identify_row(event.y)
            source_item = self.drag_data['item']

            if target_item and source_item != target_item:
                # 获取所有项目
                all_items = list(self.get_children())

                # 移除源项目
                all_items.remove(source_item)

                # 找到目标位置并插入
                target_index = all_items.index(target_item)
                all_items.insert(target_index, source_item)

                # 重新排序
                for i, item in enumerate(all_items):
                    self.move(item, '', i)

            # 清理
            self.drag_data = {'x': 0, 'y': 0,
                              'item': None, 'values': None, 'text': None}

            # 移除预览窗口
            if self.drag_window:
                self.drag_window.destroy()
                self.drag_window = None

            # 移除指示线
            for item in self.get_children():
                tags = self.item(item, 'tags')
                if tags and 'insert_pos' in tags:
                    self.item(item, tags=())


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

        self.item_to_path = {}
        self.lst_files = []
        self.path_out_floder = ""
        self.path_pal_source = ""
        self.path_pal_target = ""
        self.path_template = ""

        self.current_image = None  # 保存 PhotoImage 引用

        self.only_start = ""
        self.only_end = ""

        self.image_label_width = 608
        self.image_label_height = 308
        self.theaters = [".tem", ".urb", ".sno", ".ubn", ".des", ".lun"]
        self.preset_name = []
        self.preset_value = []
        self.load_preset()

        self._init_ui()

        self.load_config()
        self.tmp_suffix = "*"+" *".join(self.theaters)

    # --------- UI ---------

    def _init_ui(self):
        self.lb_show_type = "PAGE_0"

        # ----- 文件列表 -----

        self.file_frame = ttk.Labelframe(self, text="文件列表")
        self.file_frame.place(x=10, y=10, width=880, height=365)

        self.tree = AdvancedSortableTreeview(
            self.file_frame,
            columns=("file", "preview"),
            show="headings"
        )

        self.tree.heading("file", text="文件")
        self.tree.heading("preview", text="导出名称预览")

        self.tree.column("file", width=100, anchor="w", stretch=False)
        self.tree.column("preview", width=100, anchor="w", stretch=False)

        def disable_column_resize(event):
            if self.tree.identify_region(event.x, event.y) == "separator":
                return "break"
        self.tree.bind("<Button-1>", disable_column_resize, add="+")

        # 纵向滚动条
        sb = ttk.Scrollbar(
            self.file_frame,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=sb.set)

        self.tree.place(x=10, y=10, width=200, height=292)
        sb.place(x=210, y=10, height=292)

        # 按钮
        ttk.Button(self.file_frame, text="添加",
                   command=self.btn_add_files).place(x=10, y=310, width=62, height=25)
        ttk.Button(self.file_frame, text="移除",
                   command=self.btn_remove_selected).place(x=74, y=310, width=62, height=25)
        ttk.Button(self.file_frame, text="清空全部",
                   command=self.btn_remove_all).place(x=140, y=310, width=80, height=25)

        # 右侧预览区
        self.image_label = ttk.Label(
            self.file_frame, anchor="center", relief="flat")
        self.image_label.place(
            x=246, y=8, width=self.image_label_width, height=self.image_label_height)

        self.tree.bind("<<TreeviewSelect>>", self.file_on_select)
        self.show_preview(Image.new("RGB", (10, 10), (255, 255, 255)))

        # ttk.Button(self.file_frame, text="导出",
        #            command=self.btn_run).place(x=3, y=350, width=80, height=25)

        # ----- 路径选择 -----

        self.path_frame = ttk.Labelframe(self, text="路径设置")
        self.path_frame.place(x=10, y=385, width=880, height=120)

        # 1) 批处理路径选择
        self.lb_out_floder = ttk.Label(self.path_frame, text="文件导出到目录：")
        self.lb_out_floder.place(x=10, y=5, width=120, height=25)

        self.ent_out_floder = tk.Entry(
            self.path_frame, relief="sunken", insertwidth=1)
        self.ent_out_floder.place(x=110, y=5, width=670, height=25)

        ttk.Button(
            self.path_frame, text="选择目录", command=self.btn_choose_folder
        ).place(x=790, y=5, width=80, height=25)

        # 2) 色盘选择
        self.lb_pal_source = ttk.Label(self.path_frame, text="导入地形的色盘：")
        self.lb_pal_source.place(x=10, y=35, width=120, height=25)

        self.ent_pal_source = tk.Entry(
            self.path_frame, relief="sunken", insertwidth=1)
        self.ent_pal_source.place(x=110, y=35, width=670, height=25)

        self.btn_pal_source = ttk.Button(
            self.path_frame, text="选择色盘", command=self.btn_choose_pal_input
        )
        self.btn_pal_source.place(x=790, y=35, width=80, height=25)

        # 气候转换双色盘
        self.lb_pal_target = ttk.Label(self.path_frame, text="新地形的色盘：")
        self.lb_pal_target.place(x=10, y=65, width=120, height=25)

        self.ent_pal_target = tk.Entry(
            self.path_frame, relief="sunken", insertwidth=1)
        self.ent_pal_target.place(x=110, y=65, width=670, height=25)

        self.btn_pal_target = ttk.Button(
            self.path_frame, text="选择色盘", command=self.btn_choose_pal_output
        )
        self.btn_pal_target.place(x=790, y=65, width=80, height=25)

        # 3) 模板选择
        self.lb_template = ttk.Label(self.path_frame, text="选择地形模板：")
        self.lb_template.place(x=10, y=65, width=120, height=25)

        self.ent_template = tk.Entry(
            self.path_frame, relief="sunken", insertwidth=1)
        self.ent_template.place(x=110, y=65, width=670, height=25)

        self.btn_template = ttk.Button(
            self.path_frame, text="选择模板", command=self.btn_choose_template
        )
        self.btn_template.place(x=790, y=65, width=80, height=25)

        # ----- 选项设置 -----

        # x=220, y=5,
        # x=350, y=30,

        self.setting_frame = ttk.Labelframe(self, text="导出选项")
        self.setting_frame.place(x=10, y=515, width=880, height=120)

        # 1) Checkbox 自动色盘
        self.var_auto_pal_source = tk.StringVar(value="enable")

        self.ckb_auto_pal_source = ttk.Checkbutton(
            self.setting_frame, text="自动选择色盘", variable=self.var_auto_pal_source, onvalue="enable", offvalue="disable")

        self.ckb_auto_pal_source.place(x=220, y=5, width=110, height=25)

        self.var_auto_pal_target = tk.StringVar(value="enable")
        self.ckb_auto_pal_target = ttk.Checkbutton(
            self.setting_frame, text="自动选择色盘 - 新地形", variable=self.var_auto_pal_target, onvalue="enable", offvalue="disable")

        self.ckb_auto_pal_target.place(x=220, y=30, width=160, height=25)

        # 2) Label 前缀
        self.lb_prefix = ttk.Label(self.setting_frame, text="仅转换前缀：")
        self.lb_prefix.place(x=10, y=5, width=80, height=25)

        self.ent_prefix = tk.Entry(
            self.setting_frame, relief="flat", insertwidth=1)
        self.ent_prefix.place(x=85, y=7, width=104, height=20)
        ToolTip(self.ent_prefix, "只转换带有该前缀的文件")

        # 3) Label 后缀
        self.lb_suffix = ttk.Label(self.setting_frame, text="仅转换后缀：")
        self.lb_suffix.place(x=10, y=35, width=80, height=25)

        self.ent_suffix = tk.Entry(
            self.setting_frame, relief="flat", insertwidth=1)
        self.ent_suffix.place(x=85, y=37, width=104, height=20)
        ToolTip(self.ent_suffix, "只转换带有该后缀的文件，包含文件后缀名")
        # \n符合该后缀的文件将跳过气候检查

        # 4) Label 导出名称
        self.lb_save_name = ttk.Label(self.setting_frame, text="导出文件名：")
        self.lb_save_name.place(x=10, y=65, width=80, height=25)

        self.ent_save_name = tk.Entry(
            self.setting_frame, relief="flat", insertwidth=1)
        self.ent_save_name.place(x=85, y=67, width=104, height=20)

        self.lb_preset = ttk.Label(self.setting_frame, text="导出文件命名规则：")
        self.lb_preset.place(x=220, y=67, width=120, height=25)

        self.var_preset = tk.StringVar()

        self.cb_preset = ttk.Combobox(
            self.setting_frame,
            textvariable=self.var_preset,
            values=self.preset_name,
            state="readonly")
        self.cb_preset.place(x=332, y=67, width=155, height=23)
        self.cb_preset.current(0)
        ToolTip(self.cb_preset,
                "选择导出文件名的后缀预设规则，列表中的内容可在配置文件中进行修改\n"
                "* 为： 导出文件名 + 文件序号\n"
                "文件将按顺序生成逗号分隔的多个项\n"
                "具体示例参照配置文件")

        self.btn_runbtn = ttk.Button(
            self.setting_frame, text="开始导出", command=self.btn_run)
        self.btn_runbtn.place(x=700, y=60, width=120, height=30)

    # --------- 行为逻辑 ---------

    def log(self, msg, level="INFO"):
        self.log_callback(msg, level)

    def safe_call(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            self.log(traceback.format_exc(), "ERROR")
            return None

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

    def get_export_index(self):
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
            self.log(
                "导出名称存在多个@，使用原名称\n导出名称格式应为 [文本@起始序号] 或 [文本]，只能包含 0 或 1 个 @", "WARN")
            return raw_text, 1

        text, index_str = raw_text.split("@")

        start_index = self.get_int(index_str)

        if not text or start_index is None:
            self.log(
                "导出名称中 [文本] 为空 或 [起始序号] 错误，使用原名称\n""导出名称格式应为 [文本@起始序号] 或 [文本]", "WARN")
            return raw_text, 1
        return text, start_index

    def get_export_name(self, len_files, process_index):
        '''
        获取导出名称

        :len_files:     导出文件总数
        :process_index: 导出的第 i 个文件   从 0 开始
        '''
        preset_index = int(self.var_preset.get()[:2]) - 1
        # print(preset_index, self.var_preset.get())

        use_preset = self.preset_value[preset_index].split(",")

        current_preset = use_preset[process_index % len(use_preset)]
        current_index = process_index // len(use_preset)

        text_save_name, start_index = self.get_export_index()
        if not text_save_name:
            return ""
        width = max(2, len(str(len_files + start_index - 1)))

        text_save_name = text_save_name + \
            str(current_index + start_index).zfill(width)
        rst = current_preset.replace("*", text_save_name)

        print(rst)
        return rst

    # --------- 导出图像 ---------
    def is_valid_pil_image(self, img: Image.Image):

        if img is None:
            return False

        if not isinstance(img, Image.Image):
            return False

        w, h = img.size
        if w <= 0 or h <= 0:
            return False

        if img.getbbox() is None:
            return False

        # WWSB=yes
        # 斜坡13号地形是空的

        WWSB = True
        return WWSB

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

        existing_paths = set(self.item_to_path.values())
        for f in files:
            if f in existing_paths:
                continue
            preview_name = "notaval"
            item_id = self.tree.insert(
                "", "end", values=(Path(f).name, preview_name))
            self.item_to_path[item_id] = f

        self.save_config()

    def btn_remove_selected(self):
        for item_id in self.tree.selection():
            self.tree.delete(item_id)
            del self.item_to_path[item_id]
        self.save_config()

    def btn_remove_all(self):
        if messagebox.askyesno("标题", "是否全部移除"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.item_to_path.clear()
            self.save_config()

    def btn_run(self):
        pass

    # --------- 图片预览 ---------

    def file_on_select(self, event):

        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        file = self.item_to_path[item_id]

        if self.lb_show_type == "PAGE_1" or self.lb_show_type == "PAGE_3":
            self.path_pal_source = self.ent_pal_source.get()

            if not Path(self.path_pal_source).is_file():
                return

            render_img, palette = self.render_preview(file)
            self.show_preview(render_img, palette)

        elif self.lb_show_type == "PAGE_2" or self.lb_show_type == "PAGE_4":

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

    # --------- 配置读写 ---------

    def save_config(self):
        # return
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config.optionxform = str

        if Path(SETTING_PATH).is_file():
            config.read(SETTING_PATH, encoding="utf-8")

            self.path_pal_source = str(Path(self.ent_pal_source.get()))
            self.path_pal_target = str(Path(self.ent_pal_target.get()))
            self.path_out_floder = str(Path(self.ent_out_floder.get()))
            self.path_template = str(Path(self.ent_template.get()))

        if not config.has_section(SECTION_LIST):
            config.add_section(SECTION_LIST)

        saved_list_str = '\n'.join(
            str(self.item_to_path[item_id]) for item_id in list(self.tree.get_children()))
        if self.lb_show_type == "PAGE_1":
            config.set(SECTION_LIST, DIR_TMP,
                       saved_list_str)

        if self.lb_show_type == "PAGE_2":
            config.set(SECTION_LIST, DIR_IMAGE,
                       saved_list_str)

        if self.lb_show_type == "PAGE_3":
            config.set(SECTION_LIST, DIR_TMP_CONVERT,
                       saved_list_str)

        if self.lb_show_type == "PAGE_4":
            config.set(SECTION_LIST, DIR_ZDATA,
                       saved_list_str)

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

        with open(SETTING_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    def isfile(self, some_path):
        if Path(some_path).is_file():
            return str(Path(some_path))
        return ""

    def load_config(self):
        # return
        # 读取 config

        if not Path(SETTING_PATH).exists():
            self.save_config()
            return

        config = configparser.ConfigParser()
        config.read(SETTING_PATH, encoding="utf-8")

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
        if self.lb_show_type == "PAGE_4":
            list_name = DIR_ZDATA

        raw = config.get(SECTION_LIST, list_name, fallback="")
        self.lst_files = [i for i in raw.splitlines(
        ) if i.strip() and Path(i).is_file()]
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_path.clear()
        # for f in self.lst_files:
        #     if f not in self.item_to_path:
        #         self.item_to_path.append(f)
        #         self.tree.insert(tk.END, Path(f).name)
        existing_paths = set(self.item_to_path.values())
        for f in self.lst_files:
            if f in existing_paths:
                continue
            # preview_name = self.generate_preview_name(f)
            preview_name = "notaval"
            item_id = self.tree.insert(
                "", "end", values=(Path(f).name, preview_name))
            self.item_to_path[item_id] = f

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

    def generate_preset(self):

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config.optionxform = str

        if Path(PRESET_PATH).is_file():
            config.read(PRESET_PATH, encoding="utf-8")

            self.path_pal_source = str(Path(self.ent_pal_source.get()))
            self.path_pal_target = str(Path(self.ent_pal_target.get()))
            self.path_out_floder = str(Path(self.ent_out_floder.get()))
            self.path_template = str(Path(self.ent_template.get()))

        if not config.has_section(SECTION_LIST):
            config.add_section(SECTION_LIST)
        config[SECTION_EXP_NAME] = {
            "0": "*",
            "1": "*,*a-*g",
            "2": "*,*a",
            "3": "*a",
            "4": "*,*b",
            "5": "*b"
        }
        config[SECTION_EXP_PRESET] = {
            "0": "*",
            "1": "*,*a,*b,*c,*d,*e,*f,*g",
            "2": "*,*a",
            "3": "*a",
            "4": "*,*b",
            "5": "*b"
        }

        with open(PRESET_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    def load_preset(self):

        if not Path(PRESET_PATH).exists():
            self.generate_preset()

        config = configparser.ConfigParser()
        config.read(PRESET_PATH, encoding="utf-8")

        self.preset_name = [str(int(k)+1).zfill(2)+" - "+v for
                            k, v in config[SECTION_EXP_NAME].items()]

        self.preset_value = [v for
                             k, v in config[SECTION_EXP_PRESET].items()]

        # # 2) 刷新色盘列表
        # self.path_template = self.isfile(config.get(
        #     SECTION_PATH, DIR_TEMPLATE, fallback=""))
        # self.ent_template.delete(0, tk.END)
        # self.ent_template.insert(0, self.path_template)
