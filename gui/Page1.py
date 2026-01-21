import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
# import configparser

from logic.modules import TmpFile, PalFile
# import logic.image as impt
import logic.render as render

from pathlib import Path
# import sys
# import traceback

from gui.gui import FilesTab, ToolTip


class Tab_One(FilesTab):
    def _init_ui(self):
        super()._init_ui()

        self.lb_show_type = "PAGE_1"
        # ----- 文件夹选择
        self.lb_template.place_forget()
        self.ent_template.place_forget()
        self.btn_template.place_forget()

        self.lb_pal_target.place_forget()
        self.ent_pal_target.place_forget()
        self.btn_pal_target.place_forget()

        self.ckb_auto_pal_target.place_forget()

        self.path_frame.place(x=10, y=385, width=880, height=120 - 30)
        self.setting_frame.place(x=10, y=515 - 30, width=880, height=120)

        ToolTip(self.ckb_auto_pal_source,
                "根据 TMP 文件后缀 在 [选中色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[png/bmp]")

        # 导出 Zdata
        self.var_zdata_mode = tk.StringVar(value="disable")

        self.ckb_zdata_mode = ttk.Checkbutton(
            self.setting_frame, text="Zdata 模式", variable=self.var_zdata_mode, onvalue="enable", offvalue="disable")

        self.ckb_zdata_mode.place(x=10, y=50, width=100, height=25)

        ToolTip(self.ckb_zdata_mode,
                "导出图像的 Zdata\n原始值 0-29对应图像 (0,0,0) 到 (232,232,232)")

        # 导出 PNG
        self.var_exp_png = tk.StringVar(value="enable")

        self.ckb_exp_png = ttk.Checkbutton(
            self.setting_frame, text="导出 PNG", variable=self.var_exp_png, onvalue="enable", offvalue="disable")

        self.ckb_exp_png.place(x=150, y=20, width=80, height=25)
        ToolTip(self.ckb_exp_png, "导出为 PNG 文件")

        # 导出 BMP
        self.var_exp_bmp = tk.StringVar(value="disable")

        self.ckb_exp_bmp = ttk.Checkbutton(
            self.setting_frame, text="导出 BMP", variable=self.var_exp_bmp, onvalue="enable", offvalue="disable")

        self.ckb_exp_bmp.place(x=150, y=50, width=80, height=25)
        ToolTip(self.ckb_exp_bmp, "导出为 BMP 文件")

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
        
        WWSB=True
        return WWSB
    
    def btn_run(self):
        self.safe_call(self.btn_run_safe)

    def btn_run_safe(self):
        self.path_pal_source = self.ent_pal_source.get()
        self.path_pal_source = self.ent_pal_source.get()
        self.path_out_floder = self.ent_out_floder.get()
        
        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()

        bmp = self.var_exp_bmp.get() == "enable"
        png = self.var_exp_png.get() == "enable"
        if not (bmp or png):
            messagebox.showwarning("警告", "未选择导出格式")
            return
        if not Path(self.path_pal_source).is_file():
            messagebox.showwarning("警告", "未选择色盘")
            return

        self.lst_files = self.full_paths.copy()
        # 选取的文件
        render_files = [
            str(Path(p))    # 斜杠方向
            for p in self.lst_files
            if Path(p).is_file() and
            Path(p).name.startswith(prefix) and
            Path(p).name.endswith(suffix)
        ]


        if not render_files:
            messagebox.showwarning("警告", "未选择需要导出的 TMP 文件")
            return

        self.log(f"开始导出已选择的 {len(render_files)} 个文件")
        self.save_config()
        self.load_config()

        # 调用
        log_warns = 0
        save_index = 1
        for i, file in enumerate(render_files):
            if self.path_out_floder == "":
                self.path_out_floder = str(Path(file).parent)
            # 色盘
            palette = self.get_source_pal(file)
            # print(palette)
            self.log(f"正在导出第{i+1}个文件 {file}")

            # text_save_name = self.ent_save_name.get().split("\n")[0]
            # print(self.path_out_floder)
            text_save_name, start_index = self.get_output_text_name()
            # 指定保存名称
            if not text_save_name == "":
                output_img = str(self.path_out_floder + "\\" + text_save_name +
                                 str(save_index + start_index - 1).zfill(len(str(len(render_files)))))
                save_index += 1
            else:
                # print(str(Path(file).name))
                output_img = self.path_out_floder + \
                    "\\" + str(Path(file).name)[:-4]

            tmp = TmpFile(file)

            if not Path(self.path_out_floder).exists():
                Path(self.path_out_floder).mkdir(parents=True, exist_ok=True)

            if self.var_zdata_mode.get() == "disable":
                re_image = render.render_full_png(
                                          tmp, palette, output_img,
                                          render_extra=True, out_bmp=bmp, out_png=png)
            else:
                re_image = render.render_full_ZData(
                                          tmp, output_img, out_bmp=bmp, out_png=png)
                output_img += "_z"

            if not self.is_valid_pil_image(re_image):
                self.log(f"第{i+1}个文件 {file}导出失败", "WARN")
                log_warns += 1
            else:
                self.show_preview(re_image)

                if bmp:
                    self.log(f"已导出第{i+1}个文件 {str(Path(output_img + ".bmp"))}")
                if png:
                    self.log(f"已导出第{i+1}个文件 {str(Path(output_img + ".png"))}")

        self.log(f"", "PASS")
        if log_warns == 0:
            self.log(f"已导出全部{i+1}文件\n\n", "SUCCESS")
        else:
            self.log(
                f"已导出{i+1-log_warns}/{i+1}个文件，其中{log_warns}个文件发生错误\n\n", "WARN")
