# =========================================================
# File: 003_Body_Base_Case.py
# Description: iRobapp-mini用 メインボディ（前後完全対称・蓋受けリブ追加版）
# Spec: 高さ45/幅50/長さ60の長方形 / 両サイドにピンセット用大窓(片面2つ)
#       天面サーボ×1 / 下面サーボ×1 / 下面配線穴 / 天面配線穴
#       前面(Y-30) ＆ 後ろ面(Y+30) にそれぞれ：上部USB / 中部USB / 下部サーボ穴 ＆ ネジ穴2つ
#       【新機能】3mm厚の蓋を支えるための内壁4つ角リブ（天面から3mm下がった位置）
#       左内壁アンプホルダー
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Body_Base_Case"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
screw_r_m2 = 1.1       # M2ネジ用穴（半径1.1mm）
wall_t     = 3.0       # 外壁の肉厚 3mm

# 長方形ボディの全体サイズ
body_w = 50.0          # X軸方向の幅
body_l = 60.0          # Y軸方向の長さ
body_h = 45.0          # Z軸方向の高さ

# 各種パーツ寸法（クリアランス込）
usb_w  = 11.5          # XIAO USB-Cアクセス穴幅
usb_h  = 7.0           # XIAO USB-Cアクセス穴高さ

# SG90サーボ用寸法
servo_w = 23.5         # サーボ本体の横幅
servo_t = 12.5         # サーボ本体の厚み
servo_pitch = 27.5     # ネジピッチ

# 各種配置オフセット
bottom_servo_offset_y = 10.0
wire_hole_r = 5.0

# ---------------------------------------------------------
# 1. ボディベース形状の作成（指定寸法の長方形）
# ---------------------------------------------------------
body_solid = Part.makeBox(body_w, body_l, body_h)
body_solid.translate(App.Vector(-body_w / 2.0, -body_l / 2.0, 0.0))

# ---------------------------------------------------------
# 2. くり抜き第1段階（中空の箱にする）
# ---------------------------------------------------------
inner_space = Part.makeBox(body_w - (wall_t * 2.0), body_l - (wall_t * 2.0), body_h - wall_t)
inner_space.translate(App.Vector(-(body_w - wall_t * 2.0) / 2.0, -(body_l - wall_t * 2.0) / 2.0, wall_t))
hollow_body = body_solid.cut(inner_space)

# ---------------------------------------------------------
# 3. くり抜き第2段階（外壁の窓、ネジ穴、配線大穴を削り落とす）
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 天面：1つ目のSG90サーボ穴 ＆ ネジ穴 ---
head_servo_hole = Part.makeBox(servo_t, servo_w, wall_t + 4.0)
head_servo_hole.translate(App.Vector(-servo_t / 2.0, -servo_w / 2.0, body_h - wall_t - 1.0))
cut_shapes.append(head_servo_hole)

for dy in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    h_screw = Part.makeCylinder(screw_r_m2, wall_t + 4.0, App.Vector(0, dy, body_h - wall_t - 1.0), App.Vector(0, 0, 1))
    cut_shapes.append(h_screw)

# --- (B) 天面：配線大穴（中央奥寄り） ---
top_wire_hole = Part.makeCylinder(wire_hole_r, wall_t + 4.0, App.Vector(0.0, 20.0, body_h - wall_t - 1.0), App.Vector(0, 0, 1))
cut_shapes.append(top_wire_hole)

# --- (C) 下面（底面）：2つ目のSG90サーボ穴 ＆ ネジ穴 ---
bottom_servo_hole = Part.makeBox(servo_t, servo_w, wall_t + 4.0)
bottom_servo_hole.translate(App.Vector(-servo_t / 2.0, bottom_servo_offset_y - servo_w / 2.0, -2.0))
cut_shapes.append(bottom_servo_hole)

for dy in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    b_screw = Part.makeCylinder(screw_r_m2, wall_t + 4.0, App.Vector(0, bottom_servo_offset_y + dy, -2.0), App.Vector(0, 0, 1))
    cut_shapes.append(b_screw)

# --- (D) 下面（底面）：コード逃がし用丸穴 ---
bottom_wire_hole = Part.makeCylinder(wire_hole_r, wall_t + 4.0, App.Vector(0.0, -15.0, -2.0), App.Vector(0, 0, 1))
cut_shapes.append(bottom_wire_hole)


# --- (E) 前面(Yマイナス側) と 後ろ面(Yプラス側) の穴配置 ---
# == 前面 (Y = -30.0mm の壁) ==
y_front_wall = -body_l / 2.0
cut_shapes.append(Part.makeBox(usb_w, wall_t + 4.0, usb_h).translate(App.Vector(-usb_w / 2.0, y_front_wall - 2.0, 37.0 - usb_h / 2.0)))
cut_shapes.append(Part.makeBox(usb_w, wall_t + 4.0, usb_h).translate(App.Vector(-usb_w / 2.0, y_front_wall - 2.0, 24.0)))
cut_shapes.append(Part.makeBox(servo_w, wall_t + 4.0, servo_t).translate(App.Vector(-servo_w / 2.0, y_front_wall - 2.0, 8.0)))
for dx in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    cut_shapes.append(Part.makeCylinder(screw_r_m2, 20.0, App.Vector(dx, y_front_wall - 5.0, 8.0 + servo_t / 2.0), App.Vector(0, 1, 0)))

# == 後ろ面 (Y = +30.0mm の壁) ==
y_rear_wall = body_l / 2.0
cut_shapes.append(Part.makeBox(usb_w, wall_t + 4.0, usb_h).translate(App.Vector(-usb_w / 2.0, y_rear_wall - wall_t - 2.0, 37.0 - usb_h / 2.0)))
cut_shapes.append(Part.makeBox(usb_w, wall_t + 4.0, usb_h).translate(App.Vector(-usb_w / 2.0, y_rear_wall - wall_t - 2.0, 24.0)))
cut_shapes.append(Part.makeBox(servo_w, wall_t + 4.0, servo_t).translate(App.Vector(-servo_w / 2.0, y_rear_wall - wall_t - 2.0, 8.0)))
for dx in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    cut_shapes.append(Part.makeCylinder(screw_r_m2, 20.0, App.Vector(dx, y_rear_wall + 5.0, 8.0 + servo_t / 2.0), App.Vector(0, -1, 0)))


# --- (F) 両サイド（X面）：ピンセット用大窓（片面四角2つ、計4つ） ---
window_l = 16.0
window_h = 20.0
for sign_x in [-1, 1]:
    x_pos = (body_w / 2.0 + 2.0) * sign_x
    for sign_y in [-1, 1]:
        y_pos = 14.0 * sign_y
        side_window = Part.makeBox(wall_t + 4.0, window_l, window_h)
        side_window.translate(App.Vector(x_pos - (wall_t + 4.0) / 2.0 if sign_x > 0 else x_pos, y_pos - window_l / 2.0, 12.0))
        cut_shapes.append(side_window)

# --- (G) 右側面：12mmスピーカーの音抜け用スリット ---
for i in range(3):
    z_pos = 35.0 + (i * 3.0)
    spk_slit = Part.makeBox(wall_t + 4.0, 15.0, 1.5)
    spk_slit.translate(App.Vector(body_w / 2.0 - wall_t - 1.0, -7.5, z_pos))
    cut_shapes.append(spk_slit)

# 結合処理
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

windowed_body = hollow_body.cut(cutter)

# ---------------------------------------------------------
# 4. 内側の固定ホルダー・リブの追加
# ---------------------------------------------------------
add_shapes = []

# --- (H) 【新機能】内壁の4つの角に配置する「蓋受け用リブ」 ---
# リブサイズ: 幅4mm × 長さ4mm × 高さ5mm
# 天面(45.0mm)から3mm下がった位置(Z=42.0mm)がリブの上面になるように配置します
lid_rib_size = 4.0
lid_rib_h    = 5.0
lid_rib_z    = (body_h - 3.0) - lid_rib_h  # Z = 37.0mm からスタート

# 内壁の限界座標（ここを基準にリブを密着させる）
inner_w_half = body_w / 2.0 - wall_t
inner_l_half = body_l / 2.0 - wall_t

for sx in [-1, 1]:
    for sy in [-1, 1]:
        corner_rib = Part.makeBox(lid_rib_size, lid_rib_size, lid_rib_h)
        # 4つの角に綺麗に密着するようにオフセット計算
        rx = (inner_w_half - lid_rib_size) if sx > 0 else -inner_w_half
        ry = (inner_l_half - lid_rib_size) if sy > 0 else -inner_l_half
        corner_rib.translate(App.Vector(rx, ry, lid_rib_z))
        add_shapes.append(corner_rib)


# --- (I) 内部：左内壁接地アンプホルダー ---
rib_w = 6.0
rib_t = 3.0
rib_h = 15.0
x_wall = -body_w / 2.0 + wall_t

amp_rib1 = Part.makeBox(rib_w, rib_t, rib_h)
amp_rib1.translate(App.Vector(x_wall, 10.0, 5.0))

amp_rib2 = Part.makeBox(rib_w, rib_t, rib_h)
amp_rib2.translate(App.Vector(x_wall, -13.0, 5.0))

groove_w = 4.5
groove_d = 3.0

g_cut1 = Part.makeBox(groove_w, groove_d + 1.0, rib_h + 1.0)
g_cut1.translate(App.Vector(x_wall + (rib_w - groove_w), 10.0 - 1.0, 4.5))

g_cut2 = Part.makeBox(groove_w, groove_d + 1.0, rib_h + 1.0)
g_cut2.translate(App.Vector(x_wall + (rib_w - groove_w), -13.0 + rib_t - groove_d, 4.5))

shaved_rib1 = amp_rib1.cut(g_cut1)
shaved_rib2 = amp_rib2.cut(g_cut2)

add_shapes.append(shaved_rib1)
add_shapes.append(shaved_rib2)

# すべてのリブ・ホルダーをボディと一体化
final_shape = windowed_body
for part in add_shapes:
    final_shape = final_shape.fuse(part)

# ---------------------------------------------------------
# 5. ドキュメントへの出力
# ---------------------------------------------------------
body_part = doc.addObject("Part::Feature", "Body_Base_Case")
body_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("003_Body_Base_Case.py: 出力しました。")
