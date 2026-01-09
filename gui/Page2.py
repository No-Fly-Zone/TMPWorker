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

        self.lb_show_type = "IMAGE"

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
                "使用选中模板：按当前预览模板导出全部文件\n"
                "图像文件名匹配：在图像所在文件夹中选择图像同名文件\n"
                "模板文件夹匹配：在当前选中模板所在文件夹中选择图像同名文件\n"
                "匹配时默认使用自动色盘转换对应气候")
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

        ToolTip(self.ent_save_name,
                "导出文件命名为[此处输入文本][01起始的序号].[气候名]\n对于导出地形，超过99后需要后续处理")
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

    def btn_run(self):
        self.path_pal = self.ent_pal.get()
        self.path_out_floder = self.ent_out_floder.get()
        self.path_template = self.ent_template.get()

        SAVE_ADDITION = ""

        if not Path(self.path_pal).is_file():
            messagebox.showwarning("警告", "未选择色盘")
            return

        prefix = self.ent_prefix.get().split("\n")[0]
        suffix = self.ent_suffix.get().split("\n")[0]

        if not suffix:
            suffix = tuple([".png", ".bmp"])

        self.lst_files = self.full_paths.copy()
        # 选取的文件
        render_files = [
            str(Path(p))    # 斜杠方向
            for p in self.lst_files
            if Path(p).is_file() and
            Path(p).name.startswith(prefix) and
            Path(p).name.endswith(suffix)
        ]

        # 批处理文件夹
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
            messagebox.showwarning("Warning", "Not file choosed")
            return

        self.log(f"开始导出已选择的{len(render_files)}个文件")
        # self.log(f"{render_files}")
        self.save_config()
        self.load_config()

        # 模板
        temp_mode = self.var_specify_template.get() == "使用选中模板"
        search_img_mode = self.var_specify_template.get() == "图像文件名匹配"
        search_tem_mode = self.var_specify_template.get() == "模板文件夹匹配"

        if temp_mode:
            self.log(f"使用选中模板导出")

        if search_img_mode:
            self.log(f"使用图像文件夹导出")

        if search_tem_mode:
            self.log(f"使用模板文件夹导出")

        if not (search_img_mode or temp_mode or search_tem_mode):
            messagebox.showwarning("警告", "未选择导出格式")
            return

        # 气候
        if self.var_output_theater.get() == "按选中模板气候":
            output_theaters = self.path_template[-4:]
        else:
            output_theaters = "." + self.var_output_theater.get()[3:].lower()
        # print(output_theaters)

        # 调用

        save_index = 1
        log_warns = 0
        for i, img_file in enumerate(render_files):

            import_img = img_file
            img_file_name = Path(import_img).name
            import_template = self.path_template

            tem_floder = Path(import_template).parent

            text_save_name = self.ent_save_name.get().split("\n")[0]

            # 色盘

            self.log(f"正在导出第{i+1}个文件 {import_img}")
            # 模板
            if temp_mode:

                template_tmp = import_template
                if not Path(template_tmp).is_file():
                    self.log(
                        f"文件 {import_img}\n未找到对应模板{template_tmp}", "ERROR")
                    break

                if self.var_auto_pal.get() == "enable":
                    pal_name = "iso" + output_theaters[1:] + ".pal"
                    pal_floder = Path(self.path_pal).parent
                    pal_file = pal_floder / pal_name
                    palette = PalFile(pal_file).palette
                else:
                    palette = PalFile(self.path_pal).palette

                tmp = TmpFile(template_tmp)

                re_is_size, re_size_1, re_size_2 = impt.import_image_to_tmp(
                    tmp, import_img, palette, background_index=0,
                    auto_radar=self.var_auto_radar.get() == "enable",
                    change_normal=self.var_impt_img.get() == "enable",
                    change_extra=self.var_impt_ext.get() == "enable")

                if not re_is_size:
                    self.log(
                        f"文件 {import_img}\n与模板{template_tmp}\n大小不一致！\t文件大小：{re_size_1}\t模板大小：{re_size_2}", "ERROR")
                    log_warns += 1
                    continue

                # 保存名称
                if not text_save_name == "":
                    import_save = Path(self.path_out_floder) / (text_save_name + str(save_index).zfill(
                        len(str(len(render_files)))) + output_theaters)
                    save_index += 1
                else:
                    import_save = Path(self.path_out_floder) / (
                        str(Path(import_img).name)[
                            :-4] + SAVE_ADDITION + output_theaters)
                    
                # 确保保存路径存在
                src = Path(template_tmp)
                if not Path(import_save).exists():
                    Path(import_save).parent.mkdir(parents=True, exist_ok=True)
                    with src.open("rb") as f_src, Path(import_save).open("wb") as f_dst:
                        f_dst.write(f_src.read())

                impt.save_tmpfile(tmp, import_save)
                self.log(f"已导出第{i+1}个文件 {import_save}")
                continue

            if search_img_mode:

                template_tmp = ""
                if Path(import_img[:-4] + output_theaters).is_file():
                    template_tmp = import_img[:-4] + output_theaters
                else:
                    for t in self.theaters:
                        if Path(import_img[:-4] + t).is_file():
                            template_tmp = import_img[:-4] + t
                            break
                
                if Path(template_tmp).is_file():

                    self.log(f"匹配到模板{template_tmp}", "INFO")

                    if self.var_auto_pal.get() == "enable":
                        pal_name = "iso" + output_theaters[1:] + ".pal"
                        pal_floder = Path(self.path_pal).parent
                        pal_file = pal_floder / pal_name
                        palette = PalFile(pal_file).palette
                    else:
                        palette = PalFile(self.path_pal).palette

                    template_tmp = import_img[:-4] + output_theaters

                    tmp = TmpFile(template_tmp)

                    re_is_size, re_size_1, re_size_2 = impt.import_image_to_tmp(
                        tmp, import_img, palette, background_index=0,
                        auto_radar=self.var_auto_radar.get() == "enable",
                        change_normal=self.var_impt_img.get() == "enable",
                        change_extra=self.var_impt_ext.get() == "enable")

                    if not re_is_size:
                        self.log(
                            f"文件 {import_img}\n与模板{template_tmp}\n大小不一致！\t文件大小：{re_size_1}\t模板大小：{re_size_2}", "ERROR")
                        log_warns += 1
                        continue

                    # 保存名称
                    if not text_save_name == "":
                        import_save = Path(self.path_out_floder) / (text_save_name +
                                                                    str(save_index).zfill(str(len(render_files))) + output_theaters)
                        save_index += 1
                    else:
                        import_save = Path(self.path_out_floder) / (
                            str(Path(import_img).name)[
                                :-4] + SAVE_ADDITION + output_theaters)
                        
                    # 确保保存路径存在
                    src = Path(template_tmp)
                    if not Path(import_save).exists():
                        Path(import_save).parent.mkdir(parents=True, exist_ok=True)
                        with src.open("rb") as f_src, Path(import_save).open("wb") as f_dst:
                            f_dst.write(f_src.read())

                    impt.save_tmpfile(tmp, import_save)
                    self.log(f"已导出第{i+1}个文件 {import_save}")

                else:
                    self.log(
                        f"文件 {import_img}\n未找到对应模板{import_img[:-4] + output_theaters}", "ERROR")
                    log_warns += 1
                continue

            if search_tem_mode:

                template_tmp = ""
                if Path(str(tem_floder / img_file_name[:-4]) + output_theaters).is_file():
                    template_tmp = str(tem_floder / img_file_name[:-4]) + output_theaters
                else:
                    for t in self.theaters:
                        if Path(str(tem_floder / img_file_name[:-4]) + t).is_file():
                            template_tmp = str(tem_floder / img_file_name[:-4]) + t
                            break

                if Path(template_tmp).is_file():
                    
                    self.log(f"匹配到模板{template_tmp}", "INFO")

                    if self.var_auto_pal.get() == "enable":
                        pal_name = "iso" + output_theaters[1:] + ".pal"
                        pal_floder = Path(self.path_pal).parent
                        pal_file = pal_floder / pal_name
                        palette = PalFile(pal_file).palette
                    else:
                        palette = PalFile(self.path_pal).palette

                    template_tmp = str(
                        tem_floder / img_file_name[:-4]) + output_theaters

                    tmp = TmpFile(template_tmp)

                    re_is_size, re_size_1, re_size_2 = impt.import_image_to_tmp(
                        tmp, import_img, palette, background_index=0,
                        auto_radar=self.var_auto_radar.get() == "enable",
                        change_normal=self.var_impt_img.get() == "enable",
                        change_extra=self.var_impt_ext.get() == "enable")

                    if not re_is_size:
                        self.log(
                            f"文件 {import_img}\n与模板{template_tmp}\n大小不一致！\t文件大小：{re_size_1}\t模板大小：{re_size_2}", "ERROR")
                        log_warns += 1
                        continue

                    # 保存名称
                    if not text_save_name == "":
                        import_save = Path(self.path_out_floder) / (text_save_name + str(
                            save_index).zfill(str(len(render_files))) + output_theaters)
                        save_index += 1
                    else:
                        import_save = Path(self.path_out_floder) / \
                            str(Path(import_img).name)[
                                :-4] + SAVE_ADDITION + output_theaters
                        
                    # 确保保存路径存在
                    src = Path(template_tmp)
                    if not Path(import_save).exists():
                        Path(import_save).parent.mkdir(parents=True, exist_ok=True)
                        with src.open("rb") as f_src, Path(import_save).open("wb") as f_dst:
                            f_dst.write(f_src.read())

                    impt.save_tmpfile(tmp, import_save)
                    self.log(f"已导出第{i+1}个文件 {import_save}")

                else:
                    self.log(
                        f"文件 {import_img}\n未找到对应模板{str(tem_floder / img_file_name[:-4]) + output_theaters}", "ERROR")
                    log_warns += 1

        self.log(f"", "PASS")
        if log_warns == 0:
            self.log(f"已导出全部{i+1}文件\n\n", "SUCCESS")
        else:
            self.log(
                f"已导出{i+1-log_warns}/{i+1}个文件，其中{log_warns}个文件发生错误\n\n", "WARN")
