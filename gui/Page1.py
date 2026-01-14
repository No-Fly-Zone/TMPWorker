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

        self.ent_template.place_forget()
        self.btn_template.place_forget()
        self.ent_pal_output.place_forget()
        self.btn_pal_output.place_forget()
        self.ckb_auto_pal_change.place_forget()

        ToolTip(self.ckb_auto_pal,
                "根据 TMP 文件后缀 在 [选中色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")
        # ----- 选项设置

        # 按钮区
        ttk.Button(self.btn_frame, text="添加",
                   command=self.btn_add_files).place(x=3, y=0, width=80, height=25)
        ttk.Button(self.btn_frame, text="移除",
                   command=self.btn_remove_selected).place(x=3, y=30, width=80, height=25)
        ttk.Button(self.btn_frame, text="清空全部",
                   command=self.btn_remove_all).place(x=3, y=60, width=80, height=25)
        ttk.Button(self.btn_frame, text="导出",
                   command=self.btn_run).place(x=3, y=110, width=80, height=25)

        # 导出设置
        self.ckb_frame.place(x=270, y=90, width=500, height=300)

        # 导出 PNG
        self.var_exp_png = tk.StringVar(value="enable")

        self.ckb_exp_png = ttk.Checkbutton(
            self.ckb_frame, text="导出 PNG", variable=self.var_exp_png, onvalue="enable", offvalue="disable")

        self.ckb_exp_png.place(x=0, y=25, width=80, height=25)
        ToolTip(self.ckb_exp_png, "导出为 PNG 文件")

        # 导出 BMP
        self.var_exp_bmp = tk.StringVar(value="disable")

        self.ckb_exp_bmp = ttk.Checkbutton(
            self.ckb_frame, text="导出 BMP", variable=self.var_exp_bmp, onvalue="enable", offvalue="disable")

        self.ckb_exp_bmp.place(x=0, y=50, width=80, height=25)
        ToolTip(self.ckb_exp_bmp, "导出为 BMP 文件")

        # 导出 Zdata
        self.var_zdata_mode = tk.StringVar(value="disable")

        self.ckb_zdata_mode = ttk.Checkbutton(
            self.ckb_frame, text="Zdata 模式", variable=self.var_zdata_mode, onvalue="enable", offvalue="disable")

        self.ckb_zdata_mode.place(x=0, y=75, width=100, height=25)

        ToolTip(self.ckb_zdata_mode,
                "导出图像的 Zdata\n原始值 0-29对应图像 (0,0,0) 到 (232,232,232)")

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[png/bmp]")

    # def file_on_select(self, event):
    #     if not self.lb_files.curselection():
    #         return

    #     self.path_pal = self.ent_pal.get()

    #     if not Path(self.path_pal).is_file():
    #         return
    #     index = self.lb_files.curselection()[0]
    #     file = self.full_paths[index]

    #     render_img, palette = self.render_preview(file)
    #     self.show_preview(render_img, palette)

    # # 图片预览
    # def render_preview(self, file):
    #     export_img = file[:-4] + ".png"

    #     if self.var_auto_pal.get() == "enable":
    #         pal_name = "iso" + file[-3:] + ".pal"

    #         print(pal_name)
    #         self.path_pal = self.ent_pal.get()
    #         pal_floder = Path(self.path_pal).parent
    #         pal_file = pal_floder / pal_name

    #         palette = PalFile(pal_file).palette
    #     else:
    #         palette = PalFile(self.path_pal).palette
    #     tmp = TmpFile(file)

    #     if self.var_zdata_mode.get() == "disable":
    #         render_img = render.render_full_png(
    #             tmp, palette, export_img,
    #             render_extra=True, out_bmp=False, out_png=False)
    #     else:
    #         render_img = render.render_full_ZData(tmp, export_img)
    #     return render_img, palette

    # def show_preview(self, render_img, palette=None):

    #     # 填充边框颜色
    #     border_color1 = (255, 255, 255, 255) if render_img.mode == "RGBA" else (
    #         255, 255, 255)
    #     border_color2 = (225, 225, 225, 255) if render_img.mode == "RGBA" else (
    #         225, 225, 225)

    #     p_width = self.image_label_width - 8
    #     p_height = self.image_label_height - 8

    #     if not palette == None:
    #         render_img = render_img.copy()
    #         pixels = render_img.load()

    #         old_color = palette[0]
    #         new_color = border_color1

    #         for x in range(render_img.width):
    #             for y in range(render_img.height):
    #                 if pixels[x, y] == old_color:
    #                     pixels[x, y] = new_color

    #     # 根据预览大小缩放
    #     max_w = self.image_label_width - 4
    #     max_h = self.image_label_height - 4

    #     width, height = render_img.size
    #     if width > max_w:
    #         render_img = render_img.resize(
    #             (max_w, max(int(height * max_w / width), 1)), Image.LANCZOS)

    #     width, height = render_img.size
    #     if height > max_h:
    #         render_img = render_img.resize(
    #             (max(int(width * max_h / height), 1), max_h), Image.LANCZOS)

    #     temp_img = Image.new(
    #         render_img.mode, (p_width + 2, p_height + 2), border_color1)

    #     w1, h1 = temp_img.size
    #     w2, h2 = render_img.size
    #     temp_img.paste(render_img, (int(0.5*(w1-w2)), int(0.5*(h1-h2))))

    #     preview_img = Image.new(
    #         render_img.mode, (p_width + 4, p_height + 4), border_color2)
    #     preview_img.paste(temp_img, (1, 1))

    #     self.current_image = ImageTk.PhotoImage(preview_img)
    #     self.image_label.config(image=self.current_image)

    # --------- 导出图像 ---------

    def btn_run(self):
        self.path_pal = self.ent_pal_input.get()
        self.path_pal = self.ent_pal_input.get()
        self.path_out_floder = self.ent_out_floder.get()

        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()

        bmp = self.var_exp_bmp.get() == "enable"
        png = self.var_exp_png.get() == "enable"
        if not (bmp or png):
            messagebox.showwarning("警告", "未选择导出格式")
            return
        if not Path(self.path_pal).is_file():
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

        # # 批处理文件夹
        # if not suffix:
        #     suffix = tuple(self.theaters.copy())
        # if not self.path_out_floder == "" and Path(self.path_out_floder).is_dir():
        #     floder_files = [
        #         str(p)
        #         for p in Path(self.path_out_floder).iterdir()
        #         if p.is_file() and
        #         (str(p) not in render_files) and
        #         p.name.startswith(prefix) and
        #         p.name.endswith(suffix)
        #     ]
        #     render_files += floder_files
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
            palette = self.get_palette(file_name=file)
            # print(palette)
            self.log(f"正在导出第{i+1}个文件 {file}")

            # text_save_name = self.ent_save_name.get().split("\n")[0]
            print(self.path_out_floder)
            text_save_name, start_index = self.get_output_text_name()
            # 指定保存名称
            if not text_save_name == "":
                output_img = str(self.path_out_floder + "\\" + text_save_name +
                                 str(save_index + start_index - 1).zfill(len(str(len(render_files)))))
                save_index += 1
            else:
                print(str(Path(file).name))
                output_img = self.path_out_floder + \
                    "\\" + str(Path(file).name)[:-4]

            tmp = TmpFile(file)

            if not Path(self.path_out_floder).exists():
                Path(self.path_out_floder).mkdir(parents=True, exist_ok=True)

            if self.var_zdata_mode.get() == "disable":
                re_image = self.safe_call(render.render_full_png,
                                          tmp, palette, output_img,
                                          render_extra=True, out_bmp=bmp, out_png=png)
            else:
                re_image = self.safe_call(render.render_full_ZData,
                                          tmp, output_img, out_bmp=bmp, out_png=png)
                output_img += "_z"

            if re_image == None:
                self.log(f"第{i+1}个文件 {file}导出失败", "WARN")
                log_warns += 1
            else:
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
