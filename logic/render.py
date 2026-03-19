

from PIL import Image, ImageDraw, ImageFont
from logic.modules import TmpTile, TmpFile

LANDTYPES = [
#   0           1           2           3           4           5
    "Clear",    "Clear",    "Ice",      "Ice",      "Ice",      "Tunnel",
#   6           7           8           9           10          11
    "Railroad", "Rock",     "Rock",     "Water",    "Beach",    "Road",
#   12          13          14          15
    "Road",     "Clear",    "Rough",    "Cliff"
]

LANTYPE_COLORS = [
  # "Clear",    "Clear",    "Ice",      "Ice",      "Ice",      "Tunnel",
    "#95ff57","#95ff57","#000000","#000000","#000000","#866e00ff",
  # "Railroad", "Rock",     "Rock",     "Water",    "Beach",    "Road",
    "#D3D3D3","#ff4a4a","#ff4a4a","#9fdee0","#00ff2a","#e562ff",
  # "Road",     "Clear",    "Rough",    "Cliff"
    "#e562ff","#95ff57","#FF9F22","#ff5959"
]
# "Clear",
# "Road",
# "Rough",
# "Water",
# "Rock",
# "Tiberium",
# "Beach",
# "Tunnel",
# "Railroad",
# "Cliff",
# "Wall",
# "Ore",
# "River",
# "Ice",
# "Weeds",


# 0, 1 or 13 is used for Clear. Ice uses 0 to 4. 
# Tunnel is 5. Railroad is 6. Rock uses 7 or 8 (15 is also used as rock in cliff tiles). 
# Water is 9. Beach is 10. Road uses 11 or 12. Rough is 14. Cliff is 15.
# Wall, Tiberium and Weeds don't have numbers but are processed based on their overlay placed on the cells.

def map_z_byte(b):
    Z_DATA_LEVEL_MUIL = 8
    v = int(max(0, min(255, b * Z_DATA_LEVEL_MUIL)))
    return (v, v, v, 255)


def draw_landtype(img: Image,land_type):

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()

    # 写入文字
    text_land = str(land_type) + " " + LANDTYPES[land_type]
    w, h = img.size
    bbox = draw.textbbox((0, 0), text_land, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    position = ((w - text_w) // 2, (h - text_h) // 2)
    x, y = position
    draw.text((x+1, y-4), text_land, font=font, fill=(0, 0, 0))  # 阴影
    draw.text((x, y-5), text_land, font=font, fill=LANTYPE_COLORS[land_type])  # 正文
    # draw.text(position, text, fill=(255, 255, 255), font=font)    

    return img

def tile_image(tile: TmpTile, bw, bh, palette, background_index=0, render_land_type=False):
    """
    渲染单个 tile 的 Normal 部分图像 (TileData) 
    """
    # find = False
    br, bg, bb, _ = palette[0]
    img = Image.new("RGBA", (bw, bh), (br, bg, bb, 0))
    px = img.load()

    ptr = 0
    x = bw // 2
    width = 0
    half = bh // 2

    # 上半
    for y in range(half):
        width += 4
        x -= 2
        for i in range(width):
            if ptr >= len(tile.TileData):
                break
            cindex = tile.TileData[ptr]
            # if cindex in RE_INDEX:
            #     # print(cindex)
            #     find = True
            ptr += 1
            if cindex != background_index:
                r, g, b, a = palette[cindex]
                px[x + i, y] = (r, g, b, a)
    # 下半
    for y in range(half, bh):
        width -= 4
        x += 2
        for i in range(width):
            if ptr >= len(tile.TileData):
                break
            cindex = tile.TileData[ptr]
            # if cindex in RE_INDEX:
            #     # print(cindex)
            #     find = True
            ptr += 1
            if cindex != background_index:
                r, g, b, a = palette[cindex]
                px[x + i, y] = (r, g, b, a)


    if render_land_type:
        img = draw_landtype(img,int(tile.LandType))

    return img  # , find


def extra_image(tile: TmpTile, palette, background_index=0):
    """
    渲染单个 tile 的 Extra 部分图像 (ExtraData)
    返回 (img, extra_w, extra_h)
    """
    if tile.ExtraData is None or tile.ExtraWidth == 0 or tile.ExtraHeight == 0:
        return None, 0, 0
    # find = False
    w = abs(tile.ExtraWidth)
    h = abs(tile.ExtraHeight)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    ptr = 0
    for y in range(h):
        for x in range(w):
            if ptr >= len(tile.ExtraData):
                break
            idx = tile.ExtraData[ptr]
            # if idx in RE_INDEX:
            #     # print(idx)
            #     find = True
            ptr += 1
            if idx != background_index:
                r, g, b, a = palette[idx]
                px[x, y] = (r, g, b, a)
    return img, w, h  # , find


def render_full_png(tmp:TmpFile, palette, output_img, render_extra=True, out_png=True, out_bmp=False,show_landtype=False):
    """
    组合单个 tile 的 Normal 和 Extra 图像并保存
    返回 img 作为界面预览
    """
    background_index = 0
    X, Y, R, B = tmp.compute_canvas_bounds()
    w = R - X
    h = B - Y

    if w == 0 or h == 0:
        # 防止空画布
        save_canvas = Image.new("RGBA", (w, h))
        return save_canvas

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    half = tmp.BlockHeight // 2

    # render order: TileData -> ExtraData overlay -> ZData overlay (if requested)
    for tile in tmp.tiles:
        if tile is None:
            continue

        # tile image
        tile_img = tile_image(tile, tmp.BlockWidth, tmp.BlockHeight, palette, background_index,render_land_type=show_landtype)
        ox = tile.X - X
        oy = tile.Y - tile.Height * half - Y
        canvas.alpha_composite(tile_img, (ox, oy))

        # ExtraData overlay
        if render_extra and tile.has_extra and tile.ExtraData is not None:
            extra_img, ew, eh = extra_image(tile, palette, background_index)
            if extra_img:
                ex = tile.ExtraX - X
                ey = tile.ExtraY - tile.Height * half - Y
                canvas.alpha_composite(extra_img, (ex, ey))

    # ---------- 填充背景色 ----------
    r, g, b, a = palette[background_index]
    w, h = canvas.size
    pixels = list(canvas.getdata())  # 扁平化像素
    new_pixels = [(r, g, b, a) if px[3] == 0 else px for px in pixels]

    save_canvas = Image.new("RGBA", (w, h))
    save_canvas.putdata(new_pixels)

    # ---------- 保存输出 ----------
    if out_png:
        save_canvas.save(output_img + '.png')
        print("Saved:", output_img + '.png')

    if out_bmp:
        save_canvas.save(output_img + '.bmp')
        print("Saved:", output_img + '.bmp')

    return save_canvas



def tile_Zdata(tile: TmpTile, bw, bh):
    """
    把 tile.ZData（如果存在）渲染为一张图片：
    - 值 0 视为透明
    """
    if tile.ZData is None:
        return None

    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    px = img.load()
    ptr = 0
    x = bw // 2
    width = 0
    half = bh // 2

    for y in range(half):
        width += 4
        x -= 2
        for i in range(width):
            if ptr >= len(tile.ZData):
                break
            zb = tile.ZData[ptr]
            ptr += 1
            if zb == 0:
                continue
            px[x + i, y] = map_z_byte(zb)

    for y in range(half, bh):
        width -= 4
        x += 2
        for i in range(width):
            if ptr >= len(tile.ZData):
                break
            zb = tile.ZData[ptr]
            ptr += 1
            if zb == 0 or zb == 205:
                continue
            px[x + i, y] = map_z_byte(zb)

    return img


def extra_ZData(tile: TmpTile):
    """
    渲染 ExtraZData（rectangular），按 ExtraWidth x ExtraHeight，0/205 视为透明。
    返回 (img, w, h)
    """
    if tile.ExtraZData is None or tile.ExtraWidth == 0 or tile.ExtraHeight == 0:
        return None, 0, 0
    w = abs(tile.ExtraWidth)
    h = abs(tile.ExtraHeight)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    ptr = 0

    for y in range(h):
        for x in range(w):
            if ptr >= len(tile.ExtraZData):
                break
            zb = tile.ExtraZData[ptr]
            ptr += 1
            if zb == 0 or zb == 205:
                continue
            px[x, y] = map_z_byte(zb)
    return img, w, h

def render_full_ZData(tmp, out_z_png, out_png=False, out_bmp=False):
    """
    渲染 ZData 画布，并填充透明像素为红色
    """
    X, Y, R, B = tmp.compute_canvas_bounds()
    w = R - X
    h = B - Y

    if w == 0 or h == 0:
        return Image.new("RGBA", (w, h))

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    half = tmp.BlockHeight // 2

    # 渲染 tile 的 ZData 和 ExtraZData
    for tile in tmp.tiles:
        if tile is None:
            continue

        if tile.has_z and tile.ZData:
            z_img = tile_Zdata(tile, tmp.BlockWidth, tmp.BlockHeight)
            if z_img:
                ox = tile.X - X
                oy = tile.Y - tile.Height * half - Y
                canvas.alpha_composite(z_img, (ox, oy))

        if tile.ExtraZData:
            ez_img, ew, eh = extra_ZData(tile)
            if ez_img:
                ex = tile.ExtraX - X
                ey = tile.ExtraY - tile.Height * half - Y
                canvas.alpha_composite(ez_img, (ex, ey))

    # ---------- 填充透明像素为红色 (255, 0, 0, 255) ----------
    r, g, b, a = 255, 0, 0, 255
    pixels = list(canvas.getdata())
    new_pixels = [(r, g, b, a) if px[3] == 0 else px for px in pixels]

    save_canvas = Image.new("RGBA", (w, h))
    save_canvas.putdata(new_pixels)

    # ---------- 保存 ----------
    if out_png:
        save_canvas.save(out_z_png + '_z.png')
        print("Saved:", out_z_png + '_z.png')

    if out_bmp:
        save_canvas.save(out_z_png + '_z.bmp')
        print("Saved:", out_z_png + '_z.bmp')

    return save_canvas
