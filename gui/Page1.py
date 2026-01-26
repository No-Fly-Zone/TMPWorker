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

        self.ckb_zdata_mode.place(x=220, y=30, width=100, height=25)

        ToolTip(self.ckb_zdata_mode,
                "导出图像的 Zdata\n原始值 0-29对应图像 (0,0,0) 到 (232,232,232)")

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

    def btn_run(self):
        self.safe_call(self.btn_run_safe)

    def btn_run_safe(self):

        # ========= 基础参数 =========
        pal_source = self.ent_pal_source.get()
        out_folder = self.ent_out_floder.get().strip()

        prefix = self.ent_prefix.get().split("\n")[0].strip()
        suffix = self.ent_suffix.get().split("\n")[0].strip()

        export_bmp = self.var_exp_bmp.get() == "enable"
        export_png = self.var_exp_png.get() == "enable"

        # ========= 参数校验 =========
        if not (export_bmp or export_png):
            messagebox.showwarning("警告", "未选择导出格式")
            return

        if not Path(pal_source).is_file():
            messagebox.showwarning("警告", "未选择色盘")
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
            messagebox.showwarning("警告", "未选择需要导出的 TMP 文件")
            return

        total = len(render_files)
        self.log(f"开始导出已选择的 {total} 个文件")
        self.save_config()
        self.load_config()

        failed_count = 0

        # ========= 主循环 =========
        for index, img_path in enumerate(render_files, start=1):

            # 默认输出目录
            target_dir = Path(out_folder) if out_folder else img_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)

            palette = self.get_source_pal(str(img_path))
            self.log(f"正在导出第{index}个文件 {img_path}")

            # 输出文件名
            export_name = self.get_export_name(total, index - 1)
            base_name = export_name if export_name else img_path.stem
            output_base = target_dir / base_name

            tmp_file = TmpFile(str(img_path))

            # ========= 渲染 =========
            if self.var_zdata_mode.get() == "disable":
                image = render.render_full_png(
                    tmp_file,
                    palette,
                    str(output_base),
                    render_extra=True,
                    out_bmp=export_bmp,
                    out_png=export_png
                )
            else:
                image = render.render_full_ZData(
                    tmp_file,
                    str(output_base),
                    out_bmp=export_bmp,
                    out_png=export_png
                )
                output_base = Path(f"{output_base}_z")

            # ========= 结果处理 =========
            if not self.is_valid_pil_image(image):
                self.log(f"第{index}个文件导出失败：{img_path}", "WARN")
                failed_count += 1
                continue

            self.show_preview(image)

            if export_bmp:
                self.log(f"已导出 BMP：{output_base.with_suffix('.bmp')}")
            if export_png:
                self.log(f"已导出 PNG：{output_base.with_suffix('.png')}")

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
