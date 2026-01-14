import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
# import configparser

from logic.modules import TmpFile, PalFile
import logic.image as impt
import logic.render as render

from pathlib import Path
# import sys
# import traceback

from gui.gui import FilesTab, ToolTip


class Tab_Three(FilesTab):
    def _init_ui(self):
        super()._init_ui()

        self.lb_show_type = "PAGE_3"

        self.ent_template.place_forget()
        self.btn_template.place_forget()

        self.btn_pal_input.config(text="原色盘")
        self.btn_pal_output.config(text="新色盘")

        ttk.Label(self.ckb_frame, text="自动色盘：").place(
            x=0, y=0, width=80, height=25)

        self.ckb_auto_pal.config(text="原地形")
        self.ckb_auto_pal.place(x=0, y=25, width=80, height=25)

        ToolTip(self.ckb_auto_pal,
                "根据 原 TMP 文件后缀 在 [原色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")
        ToolTip(self.ckb_auto_pal_change,
                "根据 需要导出的文件后缀 在 [新色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")
        # 按钮区

        ttk.Button(self.btn_frame, text="添加",
                   command=self.btn_add_files).place(x=3, y=0, width=80, height=25)
        ttk.Button(self.btn_frame, text="移除",
                   command=self.btn_remove_selected).place(x=3, y=30, width=80, height=25)
        ttk.Button(self.btn_frame, text="清空全部",
                   command=self.btn_remove_all).place(x=3, y=60, width=80, height=25)
        ttk.Button(self.btn_frame, text="导出文件",
                   command=self.btn_run).place(x=3, y=110, width=80, height=25)

        # 导出设置
        self.ckb_frame.place(x=270, y=105, width=500, height=300)

        self.lb_save_name.place(x=120)
        self.ent_save_name.place(x=178)

        self.lb_prefix.place(x=120)
        self.ent_prefix.place(x=178)

        self.lb_suffix.place(x=120)
        self.ent_suffix.place(x=178)

        ttk.Label(self.ckb_frame, text="导出模式：").place(
            x=320, y=0, width=60, height=20)

        self.var_output_theater = tk.StringVar()
        self.output_theaters_values = ["转换为"+i[1:] for i in self.theaters]

        self.cb_output_theater = ttk.Combobox(
            self.ckb_frame,
            textvariable=self.var_output_theater,
            values=self.output_theaters_values,
            state="readonly")
        ToolTip(self.cb_output_theater,
                "导出文件的气候类型")
        self.cb_output_theater.place(x=320, y=30, width=115, height=24)
        self.cb_output_theater.current(0)

        # 模板
        self.path_frame.place(height=85)

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[气候名]")
    # --------- 行为逻辑 ---------

    def btn_add_files(self):
        files = filedialog.askopenfilenames(title="选择文件",    filetypes=[
            ("TMP files", self.tmp_suffix)])
        for f in files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, Path(f).name)
        self.save_config()

    # --------- 导出图像 ---------

    def _get_palette(self, file):
        '''
        获取色盘
        '''
        if self.var_auto_pal.get() != "enable":
            return PalFile(self.path_pal).palette

        pal_name = f"iso{file[-3:]}.pal"
        pal_file = Path(self.path_pal).parent / pal_name

        if pal_file.is_file():
            return PalFile(pal_file).palette

        self.log(f"未找到色盘{pal_file}\n使用选中色盘", "WARN")
        return PalFile(self.path_pal).palette

    def _get_palette_2(self, output_theaters):
        '''
        获取色盘
        '''
        if self.var_auto_pal_change.get() != "enable":
            return PalFile(self.path_pal_change).palette

        pal_name = f"iso{output_theaters[1:]}.pal"
        pal_file = Path(self.path_pal_change).parent / pal_name

        if pal_file.is_file():
            return PalFile(pal_file).palette

        self.log(f"未找到色盘{pal_file}\n使用选中色盘", "WARN")
        return PalFile(self.path_pal_change).palette

    def _build_save_path(self, import_img, save_index, total, output_theaters):

        text_save_name, start_index = self.get_output_text_name()

        if text_save_name:
            width = len(str(total))
            name = f"{text_save_name}{str(save_index + start_index - 1).zfill(width)}{output_theaters}"
        else:
            name = f"{Path(import_img).stem}{output_theaters}"

        return Path(self.path_out_floder) / name

    def _ensure_template_copy(self, template_tmp, save_path):
        if save_path.exists():
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_tmp, "rb") as src, open(save_path, "wb") as dst:
            dst.write(src.read())

    def _process_one(self, import_img, template_tmp, palette, save_path):
        tmp = TmpFile(template_tmp)

        ok, size1, size2 = impt.import_image_to_tmp(
            tmp=tmp,
            image_path=None,
            pal=palette,
            background_index=0,
            img=import_img
        )

        if not ok:
            self.log(
                f"文件 {import_img}\n与模板{template_tmp}\n"
                f"大小不一致！\t文件大小：{size1}\t模板大小：{size2}",
                "ERROR"
            )
            return False

        self._ensure_template_copy(template_tmp, save_path)
        impt.save_tmpfile(tmp, save_path)
        return True

    def btn_run(self):

        self.path_pal = self.ent_pal_input.get()
        self.path_pal_change = self.ent_pal_output.get()
        self.path_out_floder = self.ent_out_floder.get()

        if not Path(self.path_pal).is_file():
            messagebox.showwarning("警告", "未选择色盘")
            return

        if not Path(self.path_pal_change).is_file():
            messagebox.showwarning("警告", "未选择色盘")
            return

        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()

        render_files = [
            str(Path(p))
            for p in self.full_paths
            if Path(p).is_file()
            and Path(p).name.startswith(prefix)
            and Path(p).name.endswith(suffix)
        ]

        if not render_files:
            messagebox.showwarning("Warning", "Not file choosed")
            return

        self.log(f"开始导出已选择的{len(render_files)}个文件")
        self.save_config()
        self.load_config()

        output_theaters = "." + self.var_output_theater.get()[3:].lower()

        save_index = 1
        log_warns = 0
        total = len(render_files)

        for i, file in enumerate(render_files, 1):
            self.log(f"正在导出第{i}个文件 {file}")

            tmp = TmpFile(file)
            palette = self._get_palette(file)

            re_image = self.safe_call(render.render_full_png,
                                      tmp, palette, output_img="",
                                      render_extra=True, out_bmp=False, out_png=False)
            if re_image == None:
                self.log(f"第{i+1}个文件 {file}导出失败", "WARN")
                log_warns += 1
                continue
            self.show_preview(re_image)

            palette_2 = self._get_palette_2(output_theaters)

            save_path = self._build_save_path(
                file, save_index, total, output_theaters
            )

            ok = self._process_one(
                re_image, file, palette_2, save_path
            )

            if ok:
                self.log(f"已导出第{i}个文件 {save_path}")
                save_index += 1
            else:
                log_warns += 1

        self.log("", "PASS")
        if log_warns == 0:
            self.log(f"已导出全部{total}文件\n\n", "SUCCESS")
        else:
            self.log(
                f"已导出{total - log_warns}/{total}个文件，其中{log_warns}个文件发生错误\n\n",
                "WARN"
            )
