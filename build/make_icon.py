#!/usr/bin/env python3
"""生成可爱的 wechat-digest 应用图标"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius*2, y0 + radius*2], fill=fill)
    draw.ellipse([x1 - radius*2, y0, x1, y0 + radius*2], fill=fill)
    draw.ellipse([x0, y1 - radius*2, x0 + radius*2, y1], fill=fill)
    draw.ellipse([x1 - radius*2, y1 - radius*2, x1, y1], fill=fill)

def make_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size

    # ── 背景：渐变圆角矩形 ─────────────────────────────────────────────────────
    # 手动渐变（上→下，深蓝→紫）
    top_color    = (30, 20, 60)
    bottom_color = (100, 60, 180)
    radius = int(s * 0.18)

    # 先画渐变条纹，再裁成圆角矩形
    grad_layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    for y in range(s):
        t = y / s
        c = lerp_color(top_color, bottom_color, t) + (255,)
        ImageDraw.Draw(grad_layer).line([(0, y), (s, y)], fill=c)

    # 圆角蒙版
    mask = Image.new("L", (s, s), 0)
    draw_rounded_rect(ImageDraw.Draw(mask), [0, 0, s-1, s-1], radius, 255)
    img.paste(grad_layer, mask=mask)
    draw = ImageDraw.Draw(img)

    # ── 可爱报纸身体 ──────────────────────────────────────────────────────────
    pw = int(s * 0.52)
    ph = int(s * 0.60)
    px = (s - pw) // 2
    py = int(s * 0.16)

    # 报纸白色主体（圆角）
    pr = int(s * 0.06)
    draw_rounded_rect(draw, [px, py, px+pw, py+ph], pr, (255, 255, 245, 240))

    # 顶部小折角（三角）
    fx = px + pw - int(s*0.13)
    fy = py
    fold_size = int(s * 0.14)
    draw.polygon([
        (fx, fy),
        (fx + fold_size, fy),
        (fx + fold_size, fy + fold_size),
    ], fill=(200, 195, 220, 200))
    draw.polygon([
        (fx, fy),
        (fx, fy + fold_size),
        (fx + fold_size, fy + fold_size),
    ], fill=(220, 215, 240, 240))

    # 报纸横线（内容）
    lx = px + int(pw * 0.1)
    lw = int(pw * 0.55)
    lh = max(2, int(s * 0.025))
    lc = (140, 100, 200, 200)
    for i, frac in enumerate([0.22, 0.34, 0.46, 0.58]):
        ly = py + int(ph * frac)
        lwidth = lw if i == 0 else int(lw * 0.75)
        draw.rounded_rectangle([lx, ly, lx + lwidth, ly + lh], radius=lh//2, fill=lc)

    # ── 可爱脸（贴在报纸右下角，露出来的圆脸）──────────────────────────────────
    cr = int(s * 0.22)   # 脸半径
    cx = px + pw - int(cr * 0.1)
    cy = py + ph - int(cr * 0.2)

    # 脸背景（粉紫渐变圆）
    face_layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    fd = ImageDraw.Draw(face_layer)
    for r in range(cr, 0, -1):
        t = 1 - r / cr
        fc = lerp_color((230, 200, 255), (200, 160, 240), t) + (255,)
        fd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fc)
    img = Image.alpha_composite(img, face_layer)
    draw = ImageDraw.Draw(img)

    # 脸轮廓
    draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr],
                 outline=(160, 120, 210, 200), width=max(1, int(s*0.015)))

    # 眼睛（大眼萌）
    ew = max(2, int(cr * 0.22))
    eh = max(3, int(cr * 0.30))
    ex1 = cx - int(cr * 0.38)
    ex2 = cx + int(cr * 0.18)
    ey  = cy - int(cr * 0.12)
    draw.ellipse([ex1-ew, ey-eh, ex1+ew, ey+eh], fill=(60, 40, 100, 255))
    draw.ellipse([ex2-ew, ey-eh, ex2+ew, ey+eh], fill=(60, 40, 100, 255))
    # 眼睛高光
    hw = max(1, int(ew * 0.45))
    draw.ellipse([ex1-ew+1, ey-eh+1, ex1-ew+1+hw*2, ey-eh+1+hw*2],
                 fill=(255, 255, 255, 220))
    draw.ellipse([ex2-ew+1, ey-eh+1, ex2-ew+1+hw*2, ey-eh+1+hw*2],
                 fill=(255, 255, 255, 220))

    # 嘴巴（微笑弧）
    mx = cx - int(cr * 0.30)
    my = cy + int(cr * 0.20)
    mw = int(cr * 0.60)
    mh = int(cr * 0.28)
    draw.arc([mx, my, mx+mw, my+mh], start=10, end=170,
             fill=(100, 60, 160, 230), width=max(1, int(s*0.018)))

    # 腮红
    bw = int(cr * 0.22)
    bh = int(cr * 0.14)
    draw.ellipse([ex1 - bw - int(cr*0.05), ey + eh + int(cr*0.08),
                  ex1 + bw - int(cr*0.05), ey + eh + int(cr*0.08) + bh*2],
                 fill=(255, 160, 180, 80))
    draw.ellipse([ex2 - bw + int(cr*0.10), ey + eh + int(cr*0.08),
                  ex2 + bw + int(cr*0.10), ey + eh + int(cr*0.08) + bh*2],
                 fill=(255, 160, 180, 80))

    # ── 小星星装饰 ────────────────────────────────────────────────────────────
    def star(x, y, r, color):
        for angle in range(0, 360, 72):
            a1 = math.radians(angle)
            a2 = math.radians(angle + 36)
            draw.polygon([
                (x, y),
                (x + r * math.cos(a1), y + r * math.sin(a1)),
                (x + r * 0.4 * math.cos(a2), y + r * 0.4 * math.sin(a2)),
            ], fill=color)

    if size >= 64:
        star(int(s*0.14), int(s*0.20), int(s*0.055), (255, 230, 100, 200))
        star(int(s*0.80), int(s*0.15), int(s*0.038), (255, 200, 80, 160))
        star(int(s*0.12), int(s*0.72), int(s*0.030), (200, 180, 255, 160))

    return img


def generate_ico(out_path: Path):
    # 生成256px高清版，PIL会自动缩放到各尺寸
    large = make_icon(256).convert("RGBA")
    large.save(
        str(out_path),
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print(f"  ✓ 图标已生成：{out_path}  ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    out = Path(__file__).parent / "icon.ico"   # build/icon.ico
    out.parent.mkdir(exist_ok=True)
    generate_ico(out)
