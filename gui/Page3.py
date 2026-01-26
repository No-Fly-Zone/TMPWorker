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

        self.lb_template.place_forget()
        self.ent_template.place_forget()
        self.btn_template.place_forget()

        self.btn_pal_source.config(text="选择原色盘")
        self.btn_pal_target.config(text="选择新色盘")

        self.ckb_auto_pal_source.config(text="自动选择色盘 - 原地形")
        self.ckb_auto_pal_source.place(x=10, y=20, width=160, height=25)

        ToolTip(self.ckb_auto_pal_source,
                "根据 原 TMP 文件后缀 在 [原色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")
        ToolTip(self.ckb_auto_pal_target,
                "根据 需要导出的文件后缀 在 [新色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[气候名]")

        # 导出设置

        ttk.Label(self.setting_frame, text="导出模式：").place(
            x=500, y=0, width=60, height=20)

        self.var_output_theater = tk.StringVar()
        self.output_theater_values = ["转换为"+i[1:] for i in self.theaters]

        self.cb_output_theater = ttk.Combobox(
            self.setting_frame,
            textvariable=self.var_output_theater,
            values=self.output_theater_values,
            state="readonly")
        ToolTip(self.cb_output_theater,
                "导出文件的气候类型")
        self.cb_output_theater.place(x=500, y=30, width=115, height=24)
        self.cb_output_theater.current(0)

    # --------- 行为逻辑 ---------

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

    # --------- 导出图像 ---------

    def _build_save_path(self, import_img, total, output_theater, process_index):

        text_save_name = self.get_export_name(total, process_index)

        if text_save_name:
            name = f"{text_save_name}{output_theater}"
        else:
            name = f"{Path(import_img).stem}{output_theater}"

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
            img=import_img
        )

        self.show_preview(import_img)

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
        self.safe_call(self.btn_run_safe)

    def btn_run_safe(self):
        self.path_pal_source = self.ent_pal_source.get()
        self.path_pal_target = self.ent_pal_target.get()
        self.path_out_floder = self.ent_out_floder.get()

        if not Path(self.path_pal_source).is_file():
            messagebox.showwarning("警告", "未选择色盘")
            return

        if not Path(self.path_pal_target).is_file():
            messagebox.showwarning("警告", "未选择色盘")
            return

        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()


        render_files = []
        for item_id in self.tree.get_children():
            k = self.item_to_path[item_id]
            if k.startswith(prefix) and k.endswith(suffix):
                p = Path(k)
                if p.is_file():
                    render_files.append(p)

        if not render_files:
            messagebox.showwarning("Warning", "Not file choosed")
            return

        total = len(render_files)
        self.log(f"开始导出已选择的{total}个文件")
        self.save_config()
        self.load_config()

        output_theater = "." + self.var_output_theater.get()[3:].lower()

        failed_count = 0

        for i, tmp_path in enumerate(render_files, 1):
            self.log(f"正在导出第{i}个文件 {tmp_path}")

            tmp = TmpFile(tmp_path)
            pal_source = self.get_source_pal(tmp_path)

            re_image = render.render_full_png(
                tmp, pal_source, output_img="",
                render_extra=True, out_bmp=False, out_png=False)
            if re_image == None:
                self.log(f"第{i+1}个文件 {tmp_path}导出失败", "WARN")
                failed_count += 1
                continue

            pal_target = self.get_target_pal(output_theater)

            save_path = self._build_save_path(
                tmp_path, total, output_theater, i
            )

            if self._process_one(
                re_image, tmp_path, pal_target, save_path
            ):
                self.log(f"已导出第{i}个文件 {save_path}")
            else:
                failed_count += 1

        self.log("", "PASS")

        if failed_count == 0:
            self.log(f"已导出全部{total}个文件\n\n", "SUCCESS")
        elif failed_count == total:
            self.log(
                f"全部{total}个文件导出失败！ \n\n",
                "ERROR"
            )
        else:
            self.log(
                f"已导出{total - failed_count}/{total}个文件，其中{failed_count}个文件发生错误\n\n",
                "WARN"
            )
