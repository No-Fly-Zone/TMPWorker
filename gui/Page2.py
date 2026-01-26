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


class Tab_Two(FilesTab):
    def _init_ui(self):
        super()._init_ui()

        self.lb_show_type = "PAGE_2"

        self.lb_pal_target.place_forget()
        self.ent_pal_target.place_forget()
        self.btn_pal_target.place_forget()

        self.ckb_auto_pal_target.place_forget()

        ToolTip(self.ckb_auto_pal_source,
                "根据设置的导出文件后缀在 [选中色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[气候名]")

        self.var_auto_radar = tk.StringVar(value="enable")
        self.var_impt_img = tk.StringVar(value="enable")
        self.var_impt_ext = tk.StringVar(value="enable")

        self.ckb_auto_radar = ttk.Checkbutton(
            self.setting_frame, text="自动雷达色", variable=self.var_auto_radar, onvalue="enable", offvalue="disable")
        self.ckb_auto_radar.place(x=220, y=30, width=100, height=25)
        ToolTip(self.ckb_auto_radar, "自动修改雷达色")

        self.ckb_impt_img = ttk.Checkbutton(
            self.setting_frame, text="导入图像", variable=self.var_impt_img, onvalue="enable", offvalue="disable")
        self.ckb_impt_img.place(x=350, y=5, width=100, height=25)
        ToolTip(self.ckb_impt_img, "导入 Normal 部分的图像\n取消勾选时，若模板与指定导出气候不一致，图像可能错乱")

        self.ckb_impt_ext = ttk.Checkbutton(
            self.setting_frame, text="导入额外图像", variable=self.var_impt_ext, onvalue="enable", offvalue="disable")
        self.ckb_impt_ext.place(x=350, y=30, width=100, height=25)
        ToolTip(self.ckb_impt_ext, "导入 Extra 部分的图像\n取消勾选时，若模板与指定导出气候不一致，图像可能错乱")

        # 指定模板
        self.var_specify_template = tk.StringVar()
        self.cb_specify_template = ttk.Combobox(
            self.setting_frame,
            textvariable=self.var_specify_template,
            values=("使用选中模板", "图像文件名匹配", "模板文件夹匹配"),
            state="readonly")
        ToolTip(self.cb_specify_template,
                "使用选中模板：按 [当前选中模板] 导出全部文件\n"
                "图像文件名匹配：在 [图像所在文件夹] 中选择图像同名文件\n"
                "模板文件夹匹配：在 [当前选中模板所在文件夹] 中选择图像同名文件\n"
                "匹配时默认 自动选择色盘 转换对应气候")

        ttk.Label(self.setting_frame, text="导出模式：").place(
            x=500, y=0, width=60, height=20)
        self.cb_specify_template.place(x=500, y=25, width=115, height=24)
        self.cb_specify_template.current(0)

        self.var_output_theater = tk.StringVar()
        self.output_theater_values = ["按选中模板气候"]
        self.output_theater_values += ["转换为"+i[1:] for i in self.theaters]

        self.cb_output_theater = ttk.Combobox(
            self.setting_frame,
            textvariable=self.var_output_theater,
            values=self.output_theater_values,
            state="readonly")
        ToolTip(self.cb_output_theater,
                "导出文件的气候类型")
        self.cb_output_theater.place(x=500, y=60, width=115, height=24)
        self.cb_output_theater.current(0)

    # --------- 行为逻辑 ---------

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

    # --------- 导出图像 ---------

    def _find_template(self, mode, import_img, img_stem, output_theater):
        '''
        模板查找

        mode: 匹配模式
        img_stem: 文件名
        '''

        if mode == "temp":
            return self.path_template if Path(self.path_template).is_file() else ""

        if mode == "img":
            img_path = Path(import_img)
            for t in (output_theater, *self.theaters):
                p = img_path.with_suffix(t)
                if p.is_file():
                    return str(p)

        if mode == "tem":
            base = Path(self.path_template).parent / img_stem
            for t in (output_theater, *self.theaters):
                p = base.with_suffix(t)
                if p.is_file():
                    return str(p)

        return ""

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
            tmp,
            import_img,
            palette,
            auto_radar=self.var_auto_radar.get() == "enable",
            change_normal=self.var_impt_img.get() == "enable",
            change_extra=self.var_impt_ext.get() == "enable"
        )

        self.show_preview(Image.open(import_img))

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
        self.path_out_floder = self.ent_out_floder.get()
        self.path_template = self.ent_template.get()
        self.lst_files = self.item_to_path.copy()

        if not Path(self.path_pal_source).is_file():
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

        mode_map = {
            "使用选中模板": "temp",
            "图像文件名匹配": "img",
            "模板文件夹匹配": "tem",
        }
        mode = mode_map.get(self.var_specify_template.get())

        if not mode:
            messagebox.showwarning("警告", "未选择导出格式")
            return

        if self.var_output_theater.get() == "按选中模板气候":
            save_theater = self.path_template[-4:]
        else:
            save_theater = "." + self.var_output_theater.get()[3:].lower()

        failed_count = 0

        for i, img_path in enumerate(render_files, 1):
            self.log(f"正在导出第{i}个文件 {img_path}")

            template_tmp = self._find_template(
                mode,
                img_path,
                Path(img_path).stem,
                save_theater
            )

            if not template_tmp:
                self.log(f"文件 {img_path}\n未找到对应模板", "ERROR")
                failed_count += 1
                continue

            palette = self.get_source_pal(save_theater)
            save_path = self._build_save_path(
                img_path, total, save_theater, i
            )

            if self._process_one(
                img_path, template_tmp, palette, save_path
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
