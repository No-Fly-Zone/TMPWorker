
from PIL import Image
import numpy as np
from logic.modules import TmpTile, TmpFile

def map_z_byte(b):
    Z_DATA_LEVEL_MUIL = 8
    v = int(max(0, min(255, b * Z_DATA_LEVEL_MUIL)))
    return (v, v, v, 255)

def tile_image(tile: TmpTile, bw, bh, palette, background_index=0):
    """
    渲染单个 tile 的 Normal 部分图像 (TileData) 
    """
    img = Image.new("RGBA", (bw, bh), (0,0,0,0))
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
            ptr += 1
            if cindex != background_index:
                r,g,b,a = palette[cindex]
                px[x + i, y] = (r,g,b,a)
    # 下半
    for y in range(half, bh):
        width -= 4
        x += 2
        for i in range(width):
            if ptr >= len(tile.TileData):
                break
            cindex = tile.TileData[ptr]
            ptr += 1
            if cindex != background_index:
                r,g,b,a = palette[cindex]
                px[x + i, y] = (r,g,b,a)

    return img

def extra_image(tile: TmpTile, palette, background_index=0):
    """
    渲染单个 tile 的 Extra 部分图像 (ExtraData)
    返回 (img, extra_w, extra_h)
    """
    if tile.ExtraData is None or tile.ExtraWidth == 0 or tile.ExtraHeight == 0:
        return None, 0, 0

    w = abs(tile.ExtraWidth)
    h = abs(tile.ExtraHeight)
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    px = img.load()
    ptr = 0
    for y in range(h):
        for x in range(w):
            if ptr >= len(tile.ExtraData):
                break
            idx = tile.ExtraData[ptr]
            ptr += 1
            if idx != background_index:
                r,g,b,a = palette[idx]
                px[x, y] = (r,g,b,a)
    return img, w, h

def render_full_png(tmp: TmpFile, palette, output_img, render_extra=True, out_png=True,out_bmp=False):
    """
    组合单个 tile 的 Normal 和 Extra 图像并保存
    返回 img 作为界面预览
    """
    background_index = 0
    X, Y, R, B = tmp.compute_canvas_bounds()
    w = R - X
    h = B - Y
    canvas = Image.new("RGBA", (w, h), (0,0,0,0))

    half = tmp.BlockHeight // 2

    # render order: TileData -> ExtraData overlay -> ZData overlay (if requested)
    for tile in tmp.tiles:
        if tile is None:
            continue
        # tile image
        tile_img = tile_image(tile, tmp.BlockWidth, tmp.BlockHeight, palette, background_index)
        ox = tile.X - X
        oy = tile.Y - tile.Height * half - Y
        canvas.alpha_composite(tile_img, (ox, oy))

        # ExtraData: rectangular overlay at ExtraX, ExtraY adjusted for height
        if render_extra and tile.has_extra and tile.ExtraData is not None:
            extra_img, ew, eh = extra_image(tile, palette, background_index)
            if extra_img:
                ex = tile.ExtraX - X
                ey = tile.ExtraY - tile.Height * half - Y
                canvas.alpha_composite(extra_img, (ex, ey))

    # 填充背景色
    arr = np.array(canvas)
    mask = (arr[..., 3] == 0)
    r,g,b,a = palette[background_index]
    arr[mask] = [r,g,b,a]
    save_canvas = Image.fromarray(arr, mode="RGBA")
    
    if out_png:
        save_canvas.save(output_img+'.png')
        print("Saved:", output_img+'.png')

    if out_bmp:
        save_canvas.save(output_img+'.bmp')
        print("Saved:", output_img+'.bmp')
        
    return save_canvas

def tile_Zdata(tile: TmpTile, bw, bh):
    """
    把 tile.ZData（如果存在）渲染为一张图片：
    - 值 0 视为透明
    """
    if tile.ZData is None:
        return None

    img = Image.new("RGBA", (bw, bh), (0,0,0,0))
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
            if zb == 0 or zb == 205:
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
    img = Image.new("RGBA", (w, h), (0,0,0,0))
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

def render_full_ZData(tmp: TmpFile, out_z_png, out_png=False,out_bmp=False):
    '''
    TBD

    :param out_z_png: 说明
    '''
    X, Y, R, B = tmp.compute_canvas_bounds()
    w = R - X
    h = B - Y
    canvas = Image.new("RGBA", (w, h), (0,0,0,0))
    half = tmp.BlockHeight // 2

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


    arr = np.array(canvas)
    mask = (arr[..., 3] == 0)
    r,g,b,a = [255, 0, 0, 255]
    arr[mask] = [r,g,b,a]
    save_canvas = Image.fromarray(arr, mode="RGBA")

    if out_png:
        save_canvas.save(out_z_png+'_z.png')
        print("Saved:", out_z_png+'_z.png')

    if out_bmp:
        save_canvas.save(out_z_png+'_z.bmp')
        print("Saved:", out_z_png+'_z.bmp')
        
    return save_canvas
