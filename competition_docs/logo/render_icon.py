# -*- coding: utf-8 -*-
"""把一笔TC logo渲染成PNG应用图标。改样式改这里重跑即可。

画法: 沿路径每隔几px盖一个实心圆(圆的半径=线宽一半), 圆头线条天然圆滑;
先在2倍尺寸上画,再缩小到1024抗锯齿。
"""
import math
from PIL import Image, ImageDraw

SIZE = 2048          # 超采样画布, 最后缩到 1024
STROKE = 20          # 原始线宽 (viewBox 单位)
R = STROKE / 2

# ---- 原始几何 (viewBox 240x200) ----
CROSSBAR = ((30, 58), (172, 58))
STEM = ((86, 58), (86, 182))
# C 弧: 过 P1(172,58) P2(184,148), r=48, 从 P1 逆时针(视觉)绕大圈到 P2
P1, P2, R_ARC = (172, 58), (184, 148), 48.0


def arc_center():
    """解出圆心: 到 P1/P2 都是 r。取 x 较小的那个(C 的肚子在左边)。"""
    mx, my = (P1[0] + P2[0]) / 2, (P1[1] + P2[1]) / 2
    d = math.dist(P1, P2) / 2
    h = math.sqrt(R_ARC**2 - d**2)
    ux, uy = (P2[0] - P1[0]) / (2 * d), (P2[1] - P1[1]) / (2 * d)   # 弦方向单位向量
    cx1, cy1 = mx - h * uy, my + h * ux
    return (cx1, cy1) if cx1 < mx else (mx + h * uy, my - h * ux)


CX, CY = arc_center()
TH1 = math.atan2(P1[1] - CY, P1[0] - CX)          # 起点角
TH2 = math.atan2(P2[1] - CY, P2[0] - CX)          # 终点角
SWEEP = (TH1 - TH2) % (2 * math.pi)               # 递减方向绕的总角度(大弧)

# ---- 缩放: 内容(含线宽)宽约 174 单位 → 摆到画布 60% ----
SCALE = SIZE * 0.60 / 174
OX = (SIZE - 174 * SCALE) / 2 - 20 * SCALE
OY = (SIZE - 144 * SCALE) / 2 - 48 * SCALE


def to_px(x, y):
    return (OX + x * SCALE, OY + y * SCALE)


def stamp_line(img, a, b, step=4.0):
    d = ImageDraw.Draw(img)
    ax, ay = to_px(*a)
    bx, by = to_px(*b)
    length = math.dist(a, b) * SCALE
    n = max(2, int(length / step))
    r = R * SCALE
    for i in range(n + 1):
        t = i / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        d.ellipse([x - r, y - r, x + r, y + r], fill=(0, 0, 0, 255))


def stamp_arc(img):
    d = ImageDraw.Draw(img)
    r = R * SCALE
    n = int(math.degrees(SWEEP) / 2)   # 每2度一枚
    for i in range(n + 1):
        th = TH1 - SWEEP * i / n
        x, y = to_px(CX + R_ARC * math.cos(th), CY + R_ARC * math.sin(th))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(0, 0, 0, 255))


def render(bg):
    img = Image.new("RGBA", (SIZE, SIZE), bg)
    stamp_line(img, *CROSSBAR)
    stamp_line(img, *STEM)
    stamp_arc(img)
    return img.resize((1024, 1024), Image.LANCZOS)


WHITE = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)

# 只产出 App 实际引用的两张: 传统图标(白底) + 自适应前景(透明底)
render(WHITE).convert("RGB").save("../../frontend/assets/icon/tracord_icon_1024.png")
render(CLEAR).save("../../frontend/assets/icon/tracord_foreground_1024.png")
print("rendered OK")
