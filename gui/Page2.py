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

        self.ent_pal_target.place_forget()
        self.btn_pal_target.place_forget()
        self.ckb_auto_pal_target.place_forget()

        ToolTip(self.ckb_auto_pal_source,
                "根据设置的导出文件后缀在 [选中色盘] 的文件夹中自动匹配\n格式为 isoxxx.pal 的色盘文件")

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

        self.var_auto_radar = tk.StringVar(value="enable")
        self.var_impt_img = tk.StringVar(value="enable")
        self.var_impt_ext = tk.StringVar(value="enable")

        self.ckb_auto_radar = ttk.Checkbutton(
            self.ckb_frame, text="自动雷达色", variable=self.var_auto_radar, onvalue="enable", offvalue="disable")
        self.ckb_auto_radar.place(x=0, y=25, width=100, height=25)
        ToolTip(self.ckb_auto_radar, "自动修改雷达色")

        self.ckb_impt_img = ttk.Checkbutton(
            self.ckb_frame, text="导入图像", variable=self.var_impt_img, onvalue="enable", offvalue="disable")
        self.ckb_impt_img.place(x=0, y=50, width=100, height=25)
        ToolTip(self.ckb_impt_img, "导入 Normal 部分的图像\n取消勾选时，若模板与指定导出气候不一致，图像可能错乱")

        self.ckb_impt_ext = ttk.Checkbutton(
            self.ckb_frame, text="导入额外图像", variable=self.var_impt_ext, onvalue="enable", offvalue="disable")
        self.ckb_impt_ext.place(x=0, y=75, width=100, height=25)
        ToolTip(self.ckb_impt_ext, "导入 Extra 部分的图像\n取消勾选时，若模板与指定导出气候不一致，图像可能错乱")

        # 指定模板
        self.var_specify_template = tk.StringVar()
        self.cb_specify_template = ttk.Combobox(
            self.ckb_frame,
            textvariable=self.var_specify_template,
            values=("使用选中模板", "图像文件名匹配", "模板文件夹匹配"),
            state="readonly")
        ToolTip(self.cb_specify_template,
                "使用选中模板：按 [当前选中模板] 导出全部文件\n"
                "图像文件名匹配：在 [图像所在文件夹] 中选择图像同名文件\n"
                "模板文件夹匹配：在 [当前选中模板所在文件夹] 中选择图像同名文件\n"
                "匹配时默认使用 自动色盘 转换对应气候")
        ttk.Label(self.ckb_frame, text="导出模式：").place(
            x=320, y=0, width=60, height=20)
        self.cb_specify_template.place(x=320, y=25, width=115, height=24)
        self.cb_specify_template.current(0)

        self.var_output_theater = tk.StringVar()
        self.output_theaters_values = ["按选中模板气候"]
        self.output_theaters_values += ["转换为"+i[1:] for i in self.theaters]

        self.cb_output_theater = ttk.Combobox(
            self.ckb_frame,
            textvariable=self.var_output_theater,
            values=self.output_theaters_values,
            state="readonly")
        ToolTip(self.cb_output_theater,
                "导出文件的气候类型")
        self.cb_output_theater.place(x=320, y=60, width=115, height=24)
        self.cb_output_theater.current(0)

        # 模板
        self.path_frame.place(height=85)

        ToolTip(self.ent_save_name, "格式为 [文本@起始序号] 或 [文本]，起始序号默认为 1\n"
                                    "导出文件将会命名为 [文本][起始序号].[气候名]")
    # --------- 行为逻辑 ---------

    def btn_add_files(self):
        files = filedialog.askopenfilenames(title="选择文件",    filetypes=[
            ("Image files", "*.png *.bmp"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp")
        ])
        for f in files:
            if f not in self.full_paths:
                self.full_paths.append(f)
                self.lb_files.insert(tk.END, Path(f).name)
        self.save_config()

    # --------- 导出图像 ---------

    def _find_template(self, mode, import_img, img_stem, output_theaters):
        '''
        模板查找

        mode: 匹配模式
        img_stem: 文件名
        '''

        if mode == "temp":
            return self.path_template if Path(self.path_template).is_file() else ""

        if mode == "img":
            img_path = Path(import_img)
            for t in (output_theaters, *self.theaters):
                p = img_path.with_suffix(t)
                if p.is_file():
                    return str(p)

        if mode == "tem":
            base = Path(self.path_template).parent / img_stem
            for t in (output_theaters, *self.theaters):
                p = base.with_suffix(t)
                if p.is_file():
                    return str(p)

        return ""

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
            tmp,
            import_img,
            palette,
            background_index=0,
            auto_radar=self.var_auto_radar.get() == "enable",
            change_normal=self.var_impt_img.get() == "enable",
            change_extra=self.var_impt_ext.get() == "enable"
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
        self.safe_call(self.btn_run_safe)

    def btn_run_safe(self):
        self.path_pal_source = self.ent_pal_source.get()
        self.path_out_floder = self.ent_out_floder.get()
        self.path_template = self.ent_template.get()
        self.lst_files = self.full_paths.copy()

        if not Path(self.path_pal_source).is_file():
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

        save_index = 1
        log_warns = 0
        total = len(render_files)

        for i, import_img in enumerate(render_files, 1):
            self.log(f"正在导出第{i}个文件 {import_img}")

            template_tmp = self._find_template(
                mode,
                import_img,
                Path(import_img).stem,
                save_theater
            )

            if not template_tmp:
                self.log(f"文件 {import_img}\n未找到对应模板", "ERROR")
                log_warns += 1
                continue

            palette = self.get_source_pal(save_theater)
            save_path = self._build_save_path(
                import_img, save_index, total, save_theater
            )

            ok = self._process_one(
                import_img, template_tmp, palette, save_path
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
