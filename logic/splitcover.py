

import colorsys
def generate_color(tile_id, total_tiles):
    """根据tile ID生成不同的颜色"""
    # 使用HSV颜色空间，让颜色在色相环上均匀分布
    hue = (tile_id / max(total_tiles, 1)) * 0.8  # 使用0.8而不是1.0，避免颜色太接近
    saturation = 0.7 + 0.3 * (tile_id % 3) / 2.0  # 饱和度变化
    value = 0.8 + 0.2 * (tile_id % 2)  # 明度变化
    
    # 转换为RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    
    # 转换为0-255范围并添加不透明度
    return (int(r * 255), int(g * 255), int(b * 255), 255)


def diamond_row_width(y):
    """
    给定 y (0~29)，返回该行菱形的像素宽度
    """
    if y < 15:
        return 4 + y * 4
    else:
        return  (29 - y) * 4
    
from PIL import Image

def create_ab_diamond_mask(a, b):
    DX = 30
    DY = 15
    BLOCK_W = 60
    BLOCK_H = 30

    width = 30 * (a + b)
    height = 15 * (a + b)

    bg_color = (0, 0, 124, 255)  # #00007C
    img = Image.new("RGBA", (width, height), bg_color)

    # 第一个菱形的 x 起点
    start_x = (b - 1) * DX

    i = 0
    for row in range(b):
        for col in range(a):
            # 严格按你给出的位移规则
            ox = start_x + (col - row) * DX
            oy = (row + col) * DY
            i += 1
            for y in range(BLOCK_H):
                py = oy + y

                # 最后一行不允许出现任何像素
                # if py >= height - DY:
                #     continue

                row_w = diamond_row_width(y)
                left = (BLOCK_W - row_w) // 2

                for x in range(row_w):
                    px = ox + left + x
                    if 0 <= px < width and 0 <= py < height:
                        # img.putpixel((px, py), generate_color(i,a+b))
                        img.putpixel((px, py), (0,0,0,0))

    return img


a=9
b=10
img = create_ab_diamond_mask(a, b)
fname = f"{a}x{b}.png"
img.save(fname, "PNG")