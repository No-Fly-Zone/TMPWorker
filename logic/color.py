

# # --- 颜色到 palette 索引的映射（优先精确匹配，否则最近邻） ---
# import math

# def build_palette_index_map(palette):
#     """
#     palette: list of (r,g,b,a)
#     returns: dict mapping (r,g,b) -> index, list of palette rgb tuples, and list of palette Lab tuples
#     """
#     rgb_to_index = {}
#     rgb_list = []
#     lab_list = []

#     for i, (r,g,b,a) in enumerate(palette):
#         rgb_to_index[(r,g,b)] = i
#         rgb_list.append((r,g,b))
#         # Convert RGB to Lab for CIEDE2000
#         lab_list.append(rgb_to_lab(r, g, b))

#     return rgb_to_index, rgb_list, lab_list

# def rgb_to_lab(r, g, b):
#     """Convert RGB to Lab color space via XYZ"""
#     # Normalize RGB values to 0-1
#     r = r / 255.0
#     g = g / 255.0
#     b = b / 255.0

#     # Apply gamma correction
#     r = r ** 2.2 if r > 0.04045 else r / 12.92
#     g = g ** 2.2 if g > 0.04045 else g / 12.92
#     b = b ** 2.2 if b > 0.04045 else b / 12.92

#     # Convert to XYZ using D65 illuminant
#     x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
#     y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
#     z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

#     # D65 reference white
#     x_ref = 0.95047
#     y_ref = 1.00000
#     z_ref = 1.08883

#     # Normalize XYZ
#     x = x / x_ref
#     y = y / y_ref
#     z = z / z_ref

#     # Convert to Lab
#     x = x ** (1/3) if x > 0.008856 else (7.787 * x) + (16/116)
#     y = y ** (1/3) if y > 0.008856 else (7.787 * y) + (16/116)
#     z = z ** (1/3) if z > 0.008856 else (7.787 * z) + (16/116)

#     L = (116 * y) - 16
#     a = 500 * (x - y)
#     b_val = 200 * (y - z)

#     return (L, a, b_val)

# def ciede2000(lab1, lab2):
#     """
#     Calculate CIEDE2000 color difference between two Lab colors
#     Based on the formula from Sharma et al. (2005)
#     """
#     L1, a1, b1 = lab1
#     L2, a2, b2 = lab2

#     # Constants
#     kL = 1.0  # lightness weight
#     kC = 1.0  # chroma weight
#     kH = 1.0  # hue weight

#     # Step 1: Calculate C' and h'
#     C1 = math.sqrt(a1**2 + b1**2)
#     C2 = math.sqrt(a2**2 + b2**2)
#     C_avg = (C1 + C2) / 2

#     G = 0.5 * (1 - math.sqrt((C_avg**7) / (C_avg**7 + 25**7)))

#     a1_prime = a1 * (1 + G)
#     a2_prime = a2 * (1 + G)

#     C1_prime = math.sqrt(a1_prime**2 + b1**2)
#     C2_prime = math.sqrt(a2_prime**2 + b2**2)

#     h1_prime = math.degrees(math.atan2(b1, a1_prime)) % 360
#     h2_prime = math.degrees(math.atan2(b2, a2_prime)) % 360

#     # Step 2: Calculate ΔL', ΔC', ΔH'
#     ΔL_prime = L2 - L1
#     ΔC_prime = C2_prime - C1_prime

#     h_diff = h2_prime - h1_prime
#     if abs(h_diff) <= 180:
#         Δh_prime = h_diff
#     elif h_diff > 180:
#         Δh_prime = h_diff - 360
#     else:
#         Δh_prime = h_diff + 360

#     ΔH_prime = 2 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(Δh_prime / 2))

#     # Step 3: Calculate weighting functions
#     L_avg_prime = (L1 + L2) / 2
#     C_avg_prime = (C1_prime + C2_prime) / 2

#     h_avg_prime = 0
#     if abs(h1_prime - h2_prime) <= 180:
#         h_avg_prime = (h1_prime + h2_prime) / 2
#     elif abs(h1_prime - h2_prime) > 180 and (h1_prime + h2_prime) < 360:
#         h_avg_prime = (h1_prime + h2_prime + 360) / 2
#     else:
#         h_avg_prime = (h1_prime + h2_prime - 360) / 2

#     T = (1 - 0.17 * math.cos(math.radians(h_avg_prime - 30)) +
#          0.24 * math.cos(math.radians(2 * h_avg_prime)) +
#          0.32 * math.cos(math.radians(3 * h_avg_prime + 6)) -
#          0.20 * math.cos(math.radians(4 * h_avg_prime - 63)))

#     Δθ = 30 * math.exp(-((h_avg_prime - 275) / 25) ** 2)

#     R_C = 2 * math.sqrt(C_avg_prime**7 / (C_avg_prime**7 + 25**7))
#     S_L = 1 + ((0.015 * (L_avg_prime - 50)**2) / math.sqrt(20 + (L_avg_prime - 50)**2))
#     S_C = 1 + 0.045 * C_avg_prime
#     S_H = 1 + 0.015 * C_avg_prime * T

#     R_T = -R_C * math.sin(math.radians(2 * Δθ))

#     # Step 4: Calculate ΔE00
#     term1 = ΔL_prime / (kL * S_L)
#     term2 = ΔC_prime / (kC * S_C)
#     term3 = ΔH_prime / (kH * S_H)

#     ΔE00 = math.sqrt(term1**2 + term2**2 + term3**2 + R_T * term2 * term3)

#     return ΔE00

# def find_nearest_color_index(rgb, rgb_list, lab_list):
#     """
#     Find the nearest color index using CIEDE2000 color difference
#     rgb: (r,g,b) tuple
#     rgb_list: list of (r,g,b) tuples from palette
#     lab_list: list of (L,a,b) tuples from palette
#     """
#     # Convert input RGB to Lab
#     r0, g0, b0 = rgb
#     lab0 = rgb_to_lab(r0, g0, b0)

#     best_i = 0
#     best_d = float('inf')

#     for i, lab in enumerate(lab_list):
#         d = ciede2000(lab0, lab)
#         if d < best_d:
#             best_d = d
#             best_i = i

#     return best_i


from math import sqrt


def build_palette_index_map(palette):
    """
    palette: list of (r,g,b,a)
    returns: dict mapping (r,g,b) -> index and list of palette rgb tuples
    """
    rgb_to_index = {}
    rgb_list = []
    for i, (r, g, b, a) in enumerate(palette):
        rgb_to_index[(r, g, b)] = i
        rgb_list.append((r, g, b))
    return rgb_to_index, rgb_list


def find_nearest_color_index(rgb, rgb_list):
    r0, g0, b0 = rgb
    best_i = 0
    best_d = None
    for i, (r, g, b) in enumerate(rgb_list):
        d = ColorDistance(rgb, (r, g, b))
        if best_d is None or d < best_d:
            best_d = d
            best_i = i
    return best_i


def ColorDistance(rgb1, rgb2):
    # https://www.compuphase.com/cmetric.htm
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    rmean = int((r1 + r2) / 2)
    r = int(r1 - r2)
    g = int(g1 - g2)
    b = int(b1 - b2)
    return sqrt((((512+rmean)*r*r) >> 8) + 4*g*g + (((767-rmean)*b*b) >> 8))
