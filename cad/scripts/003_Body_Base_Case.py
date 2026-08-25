# =========================================================
# File: 003_Body_Base_Case.py
# Description: iRobapp-mini用 メインボディ（スピーカーリング完全撤廃・アンプ単独仕様）
# Spec: 天面首サーボ / 天面右配線大穴 / 背面下USB / 背面上尻尾サーボ / 左内壁接地アンプホルダー
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Body_Base"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
screw_r_m2 = 1.1       # M2ネジ用穴（半径1.1mm）
wall_t     = 3.0       # 外壁の肉厚 3mm

# 土台（ボディ）の全体サイズ
body_r = 35.0          # 土台の底面半径（直径70mm）
body_h = 40.0          # 土台の高さ 40mm
top_r  = body_r - 7.0  # 天面の半径（28.0mm）

# 各種パーツ寸法（クリアランス込）
usb_w  = 11.5          # XIAO USB-Cアクセス穴幅
usb_h  = 7.0           # XIAO USB-Cアクセス穴高さ

# SG90サーボ（2個共通）用寸法
servo_w = 23.0         # サーボ本体の横幅
servo_t = 12.5         # サーボ本体の厚み
servo_pitch = 27.5     # ネジピッチ

# 天面の配線専用大穴の半径：5.0mm（直径10.0mm）
wire_hole_r = 5.0

# ---------------------------------------------------------
# 1. ボディベース形状の作成（スマートなテーパー付き円柱）
# ---------------------------------------------------------
body_solid = Part.makeCone(body_r, top_r, body_h)

# ---------------------------------------------------------
# 2. くり抜き第1段階（インナーポケットでまず中空の箱にする）
# ---------------------------------------------------------
inner_space = Part.makeCone(body_r - wall_t, top_r - wall_t, body_h - wall_t)
hollow_body = body_solid.cut(inner_space)

# ---------------------------------------------------------
# 3. くり抜き第2段階（外壁の窓、ネジ穴、配線大穴を削り落とす）
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 天面：首振り用SG90サーボを落とし込む穴とネジ穴 ---
head_servo_hole = Part.makeBox(servo_t, servo_w, wall_t + 4.0)
head_servo_hole.translate(App.Vector(-servo_t / 2.0, -servo_w / 2.0, body_h - wall_t - 2.0))
cut_shapes.append(head_servo_hole)

for dy in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    h_screw = Part.makeCylinder(screw_r_m2, wall_t + 4.0, App.Vector(0, dy, body_h - wall_t - 2.0), App.Vector(0, 0, 1))
    cut_shapes.append(h_screw)

# --- (B) 天面：001丸型液晶からのコードを引き込む独立した配線大穴 ---
top_wire_hole = Part.makeCylinder(wire_hole_r, 55.0, App.Vector(14.5, 9.0, 50.0), App.Vector(0, 0, -1))
cut_shapes.append(top_wire_hole)

# --- (C) 背面下側：XIAO用 USB-C窓 ---
usb_hole = Part.makeBox(usb_w, 25.0, usb_h)
usb_hole.translate(App.Vector(-usb_w / 2.0, -body_r - 5.0, 5.0)) 
cut_shapes.append(usb_hole)

# --- (D) 背面上側：尻尾用サーボ窓 ＆ ネジ穴 ---
tail_hole = Part.makeBox(servo_w, 20.0, servo_t)
tail_hole.translate(App.Vector(-servo_w / 2.0, -body_r - 5.0, 18.0)) 
cut_shapes.append(tail_hole)

for dx in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    t_screw = Part.makeCylinder(screw_r_m2, 20.0, App.Vector(dx, -body_r + 10.0, 18.0 + servo_t / 2.0), App.Vector(0, -1, 0))
    cut_shapes.append(t_screw)

# --- (E) 右側面：12mmスピーカーの音抜け用スリット ---
for i in range(3):
    z_pos = 15.0 + (i * 4.0)
    spk_slit = Part.makeBox(wall_t + 10.0, 2.0, 10.0)
    spk_slit.translate(App.Vector(body_r - wall_t - 5.0, -5.0, z_pos))
    cut_shapes.append(spk_slit)

# すべての窓穴を結合して一気に削る
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

windowed_body = hollow_body.cut(cutter)

# ---------------------------------------------------------
# 4. 内側の固定ホルダー・リブの追加（アンプホルダーだけを綺麗に残す仕様）
# ---------------------------------------------------------
add_shapes = []

# --- (F) 【最終微調整】内部：MAX98357Aアンプ用の左内壁接地リブ ---
# スピーカーホルダー（丸リング）は完全削除されました！
rib_w = 6.0   
rib_t = 3.0   
rib_h = 15.0  

# 1本目のリブ（Y軸のプラス側：Y = 10.0）
amp_rib1 = Part.makeBox(rib_w, rib_t, rib_h)
amp_rib1.translate(App.Vector(-28.2, 10.0, 5.0))

# 2本目のリブ（Y軸のマイナス側：Y = -13.0）
amp_rib2 = Part.makeBox(rib_w, rib_t, rib_h)
amp_rib2.translate(App.Vector(-28.2, -13.0, 5.0))

# ガイド溝を掘る（内寸幅20.0mmを維持）
groove_w = 4.5
groove_d = 3.0

g_cut1 = Part.makeBox(groove_w, groove_d + 1.0, rib_h + 1.0)
g_cut1.translate(App.Vector(-25.2, 10.0 - 1.0, 4.5))

g_cut2 = Part.makeBox(groove_w, groove_d + 1.0, rib_h + 1.0)
g_cut2.translate(App.Vector(-25.2, -13.0 + rib_t - groove_d, 4.5))

# 溝を削り取る
shaved_rib1 = amp_rib1.cut(g_cut1)
shaved_rib2 = amp_rib2.cut(g_cut2)

add_shapes.append(shaved_rib1)
add_shapes.append(shaved_rib2)

# 最後にアンプホルダーのみをボディと一体化（fuse）させる
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

print("003_Body_Base_Case.py: 出力しました！")
