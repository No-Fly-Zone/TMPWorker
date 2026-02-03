from PIL import Image
BLOCK_W = 60
BLOCK_H = 30
DX = 30
DY = 15
def compute_diamond_nm(image:Image.Image):

    width, height = image.size
    if width != 2 * height:
        return None
    
    sum_nm = int(width / 30)
    
    bg_color = image.getpixel((0, 0))    
    first_row_pixels = [image.getpixel((x, 0)) for x in range(width)]
    
    non_bg_positions = 0
    for x, pixel in enumerate(first_row_pixels,1):
        if pixel != bg_color:
            non_bg_positions = x
            break
    
    if non_bg_positions == 0:
        return None

    m = int((non_bg_positions + 1) / 30)
    n = int(sum_nm) - m
    print(n, m,sum_nm)
    
    return n, m

def compute_diamond_boxes(n, m):
    """
    返回每个菱形的逻辑索引及其在原图中的像素包围盒
    """
    boxes = []
    start_x = (m - 1) * DX

    for row in range(m):
        for col in range(n):
            x0 = start_x + (col - row) * DX
            y0 = (row + col) * DY
            boxes.append({
                "row": row,
                "col": col,
                "x0": x0,
                "y0": y0,
                "x1": x0 + BLOCK_W,
                "y1": y0 + BLOCK_H
            })
    return boxes

def split_image_by_diamond_grid(big_image, a, b):
    """
    从已存在的大图像中，按 a*b 菱形逻辑切割子区域
    """
    n, m = compute_diamond_nm(big_image)
    boxes = compute_diamond_boxes(n, m)
    results = []
    if a > n or b > m:
        return [a,b,n,m], False

    for base_row in range(0, m, b):
        for base_col in range(0, n, a):

            # 选中属于该子区域的完整菱形
            selected = [
                box for box in boxes
                if base_row <= box["row"] < base_row + b
                and base_col <= box["col"] < base_col + a
            ]

            # 边缘不足 a*b 的区域直接丢弃
            if len(selected) != a * b:
                continue

            # 计算该子区域的最小像素包围盒
            min_x = min(b["x0"] for b in selected)
            min_y = min(b["y0"] for b in selected)
            max_x = max(b["x1"] for b in selected)
            max_y = max(b["y1"] for b in selected)

            w = max_x - min_x
            h = max_y - min_y

            sub_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

            # 仅复制完整菱形的像素
            for box in selected:
                for y in range(box["y0"], box["y1"]):
                    for x in range(box["x0"], box["x1"]):
                        px = big_image.getpixel((x, y))
                        if px[3] > 0:
                            sub_img.putpixel(
                                (x - min_x, y - min_y),
                                px
                            )

            results.append(sub_img)

    return results, True
# def main():
#     # 参数示例
#     n, m = 10, 10     # 原图菱形网格
#     a, b = 2, 2     # 子区域大小（菱形）


#     path = f"rpga_image_10x10.png"
#     # 加载“已存在”的大图像
#     big_image = Image.open(path).convert("RGBA")

#     sub_images = split_image_by_diamond_grid(big_image, n, m, a, b)

#     for i, img in enumerate(sub_images):
#         fname = f"sub_{i}_{a}x{b}.png"
#         img.save(fname)
#         print(f"保存: {fname}")
# main()