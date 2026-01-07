
import struct
from PIL import Image

from logic.modules import TmpFile
import logic.color as cl
from PIL import Image


def get_radar_color(radar_count):
    """
    计算图像中雷达色，取均值
    """
    r = int(radar_count['r']/max(radar_count['count'], 1))
    g = int(radar_count['g']/max(radar_count['count'], 1))
    b = int(radar_count['b']/max(radar_count['count'], 1))

    return tuple([r, g, b])

# --- 从区域图像生成 TileData  ---


def image_region_to_tiledata(tile, region_img: Image, bw, bh, palette, background_index=0, bg_rgb=None, only_write_nonbg=True, auto_radar=False):
    """
    region_img 写入 tile 的 Normal 部分，同时判断雷达色与桥头

    only_write_nonbg:
        True  - 只有当区域像素 != 背景颜色才覆盖原来的 TileData（推荐）
        False - 无论如何都写入（若像素映射到 background_index 则写 background_index）
    """
    # 原有 TileData 转为可变 bytearray
    original = bytearray(tile.TileData)
    target = original[:]  # start from original, overwrite选定位置

    rgb_to_index, rgb_list = cl.build_palette_index_map(palette)

    radar_count = {'r': 0, 'g': 0, 'b': 0, 'count': 0}

    if bg_rgb is None:
        br, bg, bb, _ = palette[background_index]
        bg_rgb = (br, bg, bb)

    px = region_img.load()  # (x,y) -> (r,g,b,a)

    ptr = 0
    x = bw // 2
    width = 0
    half = bh // 2

    # helper to read pixel at (sx, sy) if in range; returns (r,g,b,a) or None if outside
    def get_pixel(sx, sy):
        if sx < 0 or sy < 0 or sx >= region_img.width or sy >= region_img.height:
            return None
        return px[sx, sy]

    # 上半
    for y in range(half):
        width += 4
        x -= 2
        for i in range(width):
            if ptr >= len(original):
                break
            sx = x + i
            sy = y
            p = get_pixel(sx, sy)
            if p is None:
                ptr += 1
                continue
            r, g, b, a = p

            is_nonbg = (a != 0) and ((r, g, b) != bg_rgb)
            if only_write_nonbg and not is_nonbg:
                ptr += 1
                continue
            if target[ptr] == 0:    # 忽视0号色
                ptr += 1
                continue
            radar_count['r'] += r
            radar_count['g'] += g
            radar_count['b'] += b
            radar_count['count'] += 1

            # 颜色映射为色盘
            idx = rgb_to_index.get((r, g, b))
            if idx is None:
                idx = cl.find_nearest_color_index((r, g, b), rgb_list)
            target[ptr] = idx
            ptr += 1

    # 下半
    for y in range(half, bh):
        width -= 4
        x += 2
        for i in range(width):
            if ptr >= len(original):
                break
            sx = x + i
            sy = y
            p = get_pixel(sx, sy)
            if p is None:
                ptr += 1
                continue
            r, g, b, a = p

            is_nonbg = (a != 0) and ((r, g, b) != bg_rgb)
            if only_write_nonbg and not is_nonbg:
                ptr += 1
                continue
            if target[ptr] == 0:    # 忽视0号色
                ptr += 1
                continue

            radar_count['r'] += r
            radar_count['g'] += g
            radar_count['b'] += b
            radar_count['count'] += 1

            idx = rgb_to_index.get((r, g, b))
            if idx is None:
                idx = cl.find_nearest_color_index((r, g, b), rgb_list)
            target[ptr] = idx
            ptr += 1

    if auto_radar:
        radar = get_radar_color(radar_count)
    return bytes(target), radar

# --- 从区域图像生成 ExtraData（row-major） ---


def image_region_to_extradata(tile, region_img: Image, extra_w, extra_h, palette, background_index=0, bg_rgb=None):
    """
    region_img 写入 tile 的 Extra 部分

    """
    if tile.ExtraData is None:
        original = bytearray(b'\x00' * (abs(extra_w * extra_h)))
    else:
        original = bytearray(tile.ExtraData)
        # 若 original 长度小于期望，扩展（保护性处理）
        if len(original) < abs(extra_w * extra_h):
            original.extend(b'\x00' * (abs(extra_w * extra_h) - len(original)))

    target = original[:]

    rgb_to_index, rgb_list = cl.build_palette_index_map(palette)
    if bg_rgb is None:
        br, bgc, bb, _ = palette[background_index]
        bg_rgb = (br, bgc, bb)

    px = region_img.load()

    ptr = 0
    for y in range(abs(extra_h)):
        for x in range(abs(extra_w)):
            if target[ptr] == 0:    # 忽视0号色
                ptr += 1
                continue
            if x < 0 or y < 0 or x >= region_img.width or y >= region_img.height:
                ptr += 1
                continue
            r, g, b, a = px[x, y]
            is_nonbg = (a != 0) and ((r, g, b) != bg_rgb)
            # print(bg_rgb,r,g,b)
            if not is_nonbg:
                ptr += 1
                continue
            idx = rgb_to_index.get((r, g, b))
            if idx is None:
                idx = cl.find_nearest_color_index((r, g, b), rgb_list)
            target[ptr] = idx
            ptr += 1
    return bytes(target)


def import_image_to_tmp(tmp: TmpFile, image_path: str, pal, background_index=0, change_normal=True, change_extra=True, auto_radar=False, is_bridge=False):
    """
    把 image_path 打开并裁切、映射到 tmp 的每个 Tile / Extra 部分：
      - 对 TileData：把 image 中对应 tile 区域裁切后按 diamond 顺序映回 TileData；
        覆盖条件：像素 alpha>0 且颜色 != palette[background_index]
      - 对 ExtraData：仅在非背景色像素处覆盖 ExtraData（rect）
    返回：修改后的 tmp（原地修改 tile.TileData 和 tile.ExtraData）
    """
    img = Image.open(image_path).convert("RGBA")
    # 画布边界以及 tmp 的渲染 canvas（用于坐标对齐）
    X, Y, R, B = tmp.compute_canvas_bounds()
    canvas_w = R - X
    canvas_h = B - Y
    if img.size != (canvas_w, canvas_h):
        return False, img.size, (canvas_w, canvas_h)
        raise ValueError(
            f"输入图像大小 {img.size} 与 TMP 渲染画布大小 {(canvas_w, canvas_h)} 不匹配。请传入相同尺寸的 BMP/PNG 或先调整其大小。")
    # background RGB

    br, bgc, bb, _ = pal[background_index]
    # print(f'bg{br, bgc, bb}')
    # if (br, bgc, bb) == (0, 0, 125):
    #     br, bgc, bb = 3, 3, 126
    #     # 问就是神秘Pallete studio干的

    bg_rgb = (br, bgc, bb)

    # 对每个 tile，裁切对应区域并应用到 TileData / ExtraData
    half = tmp.BlockHeight // 2
    for tile in tmp.tiles:
        if tile is None:
            continue
        # tile 区域在 canvas 上的坐标（左上）
        ox = tile.X - X
        oy = tile.Y - tile.Height * half - Y
        # 1) TileData：裁切区域大小为 (BlockWidth x BlockHeight)，原点为 (ox,oy)
        # 截取该区域（如果在边界内）
        bw = tmp.BlockWidth
        bh = tmp.BlockHeight

        left = ox
        top = oy
        right = ox + bw
        bottom = oy + bh
        region = img.crop((left, top, right, bottom))
        # 根据 region 生产新的 TileData，只有非背景像素覆盖
        new_tiledata, radar_data = image_region_to_tiledata(
            tile, region, bw, bh, pal, background_index, bg_rgb, only_write_nonbg=True, auto_radar=auto_radar)
        if change_normal:
            tile.TileData = new_tiledata

        # 如果为桥梁，则无变体图像
        if is_bridge:
            # tile.DataBitfield |= 0x04
            pass
        # 处理雷达色
        if auto_radar:
            radar_r, radar_g, radar_b = radar_data
            # print(f'radar_data: {radar_data}')
            tile.RadarRedLeft = int(radar_r)
            tile.RadarGreenLeft = int(radar_g)
            tile.RadarBlueLeft = int(radar_b)

            tile.RadarRedRight = int(radar_r)
            tile.RadarGreenRight = int(radar_g)
            tile.RadarBlueRight = int(radar_b)

        # 2) ExtraData：若 tile.has_extra，则裁切 ExtraWidth x ExtraHeight 区域并按 row-major 覆盖非背景像素
        if change_extra & tile.has_extra and tile.ExtraWidth != 0 and tile.ExtraHeight != 0:
            ew = abs(tile.ExtraWidth)
            eh = abs(tile.ExtraHeight)
            ex = tile.ExtraX - X
            ey = tile.ExtraY - tile.Height * half - Y
            extra_box = (ex, ey, ex + ew, ey + eh)
            extra_region = img.crop(extra_box)
            new_extradata = image_region_to_extradata(
                tile, extra_region, ew, eh, pal, background_index, bg_rgb)
            tile.ExtraData = new_extradata

    # print("Imported image into TMP tiles (in-memory). 修改已写入 tmp.tiles。")
    return True, 0, (0, 0)


def save_tmpfile(tmp: TmpFile, out_filename):
    """
    把 tmp 对象（其 tiles 已被修改）写为新的 TMP 文件。
    逻辑：写 header(16) + index table (Width*Height ints) 占位，
          然后顺序写每个 tile（二进制），记录 offsets，
          最后回写 index table。
    """
    with open(out_filename, "wb") as f:
        # header
        f.write(struct.pack("<4i", tmp.Width, tmp.Height,
                tmp.BlockWidth, tmp.BlockHeight))
        idx_count = tmp.Width * tmp.Height
        # placeholder for index table
        f.write(b'\x00' * (idx_count * 4))
        offsets = []
        for tile in tmp.tiles:
            if tile is None:
                offsets.append(0)
                continue
            # current position
            pos = f.tell()
            offsets.append(pos)
            data = tile.tile_to_bytes(tmp.BlockWidth, tmp.BlockHeight)
            f.write(data)
        # back to index table position and write offsets
        f.seek(16)
        f.write(struct.pack("<" + "i" * idx_count, *offsets))
    print("Saved TMP:", out_filename)
