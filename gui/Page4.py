import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
# import configparser

from logic.modules import TmpFile, PalFile
import logic.image as impt
import logic.render as render
from logic.split import split_image_by_diamond_grid
from logic.splitcover import create_ab_diamond_mask

from pathlib import Path
# import sys
# import traceback

from gui.gui import FilesTab, ToolTip


class Tab_Four(FilesTab):
    def _init_ui(self):
        super()._init_ui()

        self.lb_show_type = "PAGE_4"

        # ----- 文件夹选择
        self.lb_template.place_forget()
        self.ent_template.place_forget()
        self.btn_template.place_forget()

        self.lb_pal_target.place_forget()
        self.ent_pal_target.place_forget()
        self.btn_pal_target.place_forget()

        self.ckb_auto_pal_source.place_forget()
        self.ckb_auto_pal_target.place_forget()

        self.path_frame.place(x=10, y=385, width=880, height=120 - 30)
        self.setting_frame.place(x=10, y=515 - 30, width=880, height=120)

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[png/bmp]")

        # 导出 PNG
        self.var_exp_png = tk.StringVar(value="enable")

        self.ckb_exp_png = ttk.Checkbutton(
            self.setting_frame, text="导出 PNG", variable=self.var_exp_png, onvalue="enable", offvalue="disable")

        self.ckb_exp_png.place(x=350, y=5, width=80, height=25)
        ToolTip(self.ckb_exp_png, "导出为 PNG 文件")

        # 导出 BMP
        self.var_exp_bmp = tk.StringVar(value="disable")

        self.ckb_exp_bmp = ttk.Checkbutton(
            self.setting_frame, text="导出 BMP", variable=self.var_exp_bmp, onvalue="enable", offvalue="disable")

        self.ckb_exp_bmp.place(x=350, y=30, width=80, height=25)
        ToolTip(self.ckb_exp_bmp, "导出为 BMP 文件")

        self.var_exp_png.trace_add("write", self.refresh_export_preview)
        self.var_exp_bmp.trace_add("write", self.refresh_export_preview)

    def refresh_export_preview(self, *args):

        render_files = []

        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()

        for item_id in self.tree.get_children():
            k = self.item_to_path[item_id]
            if k.startswith(prefix) and k.endswith(suffix):
                p = Path(k)
                if p.is_file():
                    render_files.append((item_id, p))

        bmp = self.var_exp_bmp.get() == "enable"
        png = self.var_exp_png.get() == "enable"
        if not bmp and not png:
            for idx, (item_id, _) in enumerate(render_files):
                self.tree.set(item_id, "preview", "无")
            return

        if bmp and png:
            suffix = ".bmp/png"
        elif bmp:
            suffix = ".bmp"
        elif png:
            suffix = ".png"
        else:
            suffix = ""
        export_suffix = suffix

        total = len(render_files)
        for idx, (item_id, _) in enumerate(render_files):
            export_name = self.get_export_name(
                total, idx, render_files) + export_suffix
            self.tree.set(item_id, "preview", export_name)

    def btn_add_files(self):
        files = filedialog.askopenfilenames(title="选择文件",    filetypes=[
            ("Image files", "*.png *.bmp"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp")
        ])

        existing_paths = set(self.item_to_path.values())
        for f in files:
            if f in existing_paths:
                continue
            preview_name = "notaval"
            item_id = self.tree.insert(
                "", "end", values=(Path(f).name, preview_name))
            self.item_to_path[item_id] = f

        self.save_config()

    def btn_run(self):
        self.safe_call(self.btn_run_safe)

    def btn_run_safe(self):

        # ========= 基础参数 =========
        out_folder = self.ent_out_floder.get().strip()

        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()

        export_bmp = self.var_exp_bmp.get() == "enable"
        export_png = self.var_exp_png.get() == "enable"

        # ========= 参数校验 =========
        if not (export_bmp or export_png):
            messagebox.showwarning("警告", "未选择导出格式")
            return

        # ========= 导出文件 =========

        render_files = []
        for item_id in self.tree.get_children():
            k = self.item_to_path[item_id]
            if k.startswith(prefix) and k.endswith(suffix):
                p = Path(k)
                if p.is_file():
                    render_files.append(p)

        if not render_files:
            messagebox.showwarning("警告", "未选择需要导出的文件")
            return

        total = len(render_files)
        self.log(f"开始导出已选择的 {total} 个文件")
        self.save_config()
        self.load_config()

        failed_count = 0
        sub_index = 1

        for index, img_path in enumerate(render_files, 1):
            a, b = 1, 2

            target_dir = Path(out_folder) if out_folder else img_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)

            self.log(f"正在导出第{index}个文件 {img_path}")

            # 输出文件名
            export_name = self.get_export_name(total, sub_index - 1)
            base_name = export_name if export_name else img_path.stem

            big_image = Image.open(str(img_path)).convert("RGBA")
            sub_images = split_image_by_diamond_grid(big_image, a, b)
            cover = create_ab_diamond_mask(a, b)

            for i, img in enumerate(sub_images,1):
                fname = f"_{str(i).zfill(len(str(len(sub_images))))}.png"
                output_name = target_dir / (base_name + fname)
                result = Image.alpha_composite(img, cover)
                result.save(output_name)
                
                self.show_preview(result)

            output_base = str(target_dir / base_name)

            if export_bmp:
                self.log(f"已导出 BMP：{output_base}")
            if export_png:
                self.log(f"已导出 PNG：{output_base}")

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
