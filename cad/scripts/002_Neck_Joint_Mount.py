# =========================================================
# File: 002_Neck_Joint_Mount.py
# Description: iRobapp-mini用 首の上下左右(パン・チルト)関節マウント
# Spec: 頭部(001)のM2ネジ穴(27.5mmピッチ)に完全適合 / SG90を2個直角に配置
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Neck_Joint"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
screw_r_m2 = 1.1       # M2穴（半径1.1mm）
wall_t     = 3.0       # 基本壁厚 3mm

# 頭部（001）側のネジピッチ
head_screw_pitch = 27.5

# SG90サーボホルダー用の標準寸法
servo_w = 23.0         # サーボ本体の幅
servo_h = 12.8         # サーボの厚み
servo_d = 12.0         # 保持する奥行き

# ネジ穴ピッチ（SG90の耳の穴間隔）
servo_pitch = 27.5

# ---------------------------------------------------------
# 1. 形状の作成（T字型の直角サーボマウント）
# ---------------------------------------------------------
# 頭部パーツとネジ留めするための「上部水平プレート」
top_plate = Part.makeBox(8.0, 36.0, wall_t)
top_plate.translate(App.Vector(-4.0, -18.0, 0))

# 上下にうなずく（ピッチ用）サーボを固定する「垂直壁」
vert_wall = Part.makeBox(wall_t, 36.0, 24.0)
vert_wall.translate(App.Vector(-wall_t/2.0, -18.0, -24.0))

# 左右に振り向く（ヨー用）サーボを直角にドッキングするための「底部水平プレート」
bottom_plate = Part.makeBox(20.0, 36.0, wall_t)
bottom_plate.translate(App.Vector(-10.0, -18.0, -24.0))

# ベース形状を統合
main_body = top_plate.fuse(vert_wall).fuse(bottom_plate)

# ---------------------------------------------------------
# 2. くり抜き処理（各種ネジ穴 ＋ サーボポケット）
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 頭部パーツ（001）と合体するためのM2ネジ穴（2箇所：Z軸方向） ---
for dy in [-head_screw_pitch / 2.0, head_screw_pitch / 2.0]:
    h_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 4.0,
        App.Vector(0, dy, -2.0),
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(h_hole)

# --- (B) 首振り用SG90サーボを落とし込むポケット＆ネジ穴（Y軸方向） ---
# サーボ本体がすっぽり入る四角い穴
servo_pocket = Part.makeBox(servo_w, wall_t + 4.0, servo_h)
servo_pocket.translate(App.Vector(-servo_w/2.0, -18.0 - 2.0, -18.0))
cut_shapes.append(servo_pocket)

# サーボの耳を固定するためのM2ネジ穴（2箇所）
for dx in [-servo_pitch / 2.0, servo_pitch / 2.0]:
    s_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 4.0,
        App.Vector(dx, -18.0 - 2.0, -12.0),
        App.Vector(0, 1, 0) # Y軸方向に貫通
    )
    cut_shapes.append(s_hole)

# ---------------------------------------------------------
# 3. くり抜き実行とドキュメント出力
# ---------------------------------------------------------
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

final_shape = main_body.cut(cutter)

neck_part = doc.addObject("Part::Feature", "Neck_Joint_Mount")
neck_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("002_Neck_Joint_Mount.py: 首のパン・チルト用直角マウントが生成されました！")
