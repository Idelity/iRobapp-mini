# =========================================================
# File: 002_Neck_Joint_Mount.py
# Description: iRobapp-mini用 首の上下左右(パン・チルト)関節マウント
# Spec: 001/003と完全同期 / 底面にSG90サーボホーンの埋込凹み＆ネジ穴を追加
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

# SG90サーボホルダー用の標準寸法（チルトサーボ用）
servo_w = 23.0         # サーボ本体の幅
servo_h = 12.8         # サーボの厚み

# SG90付属の一文字ホーン埋め込み用パラメータ（パンサーボとの結合用）
horn_w      = 5.0      # 一文字ホーンの幅（クリアランス込み）
horn_l      = 16.0     # 一文字ホーンの長さ（クリアランス込み）
horn_depth  = 1.5      # ホーンを埋め込む深さ
horn_screw_p = 11.0    # ホーン固定用ミニネジのピッチ（中心から左右5.5mm）
horn_screw_r = 0.8     # サーボ付属ミニネジ用の下穴（半径0.8mm、直径1.6mm）

# ---------------------------------------------------------
# 1. 形状の作成（T字型の直角サーボマウント）
# ---------------------------------------------------------
# 頭部パーツとネジ留めするための「上部水平プレート」
top_plate = Part.makeBox(8.0, 36.0, wall_t)
top_plate.translate(App.Vector(-4.0, -18.0, 0))

# 上下にうなずく（ピッチ用）サーボを固定する「垂直壁」
vert_wall = Part.makeBox(wall_t, 36.0, 24.0)
vert_wall.translate(App.Vector(-wall_t/2.0, -18.0, -24.0))

# 左右に振り向く（ヨー用）サーボとドッキングするための「底部水平プレート」
# ※ホーンを埋め込むため、厚みを 3.0mm から 4.5mm に少し厚くしました
bottom_plate = Part.makeBox(20.0, 36.0, 4.5)
bottom_plate.translate(App.Vector(-10.0, -18.0, -24.0))

# ベース形状を統合
main_body = top_plate.fuse(vert_wall).fuse(bottom_plate)

# ---------------------------------------------------------
# 2. くり抜き処理（各種ネジ穴 ＋ サーボポケット ＋ 底面ホーン用スリット）
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
for dx in [-head_screw_pitch / 2.0, head_screw_pitch / 2.0]:
    s_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 4.0,
        App.Vector(dx, -18.0 - 2.0, -12.0),
        App.Vector(0, 1, 0) # Y軸方向に貫通
    )
    cut_shapes.append(s_hole)

# --- (C) 【追加修正】底面：パンサーボのホーンを埋め込むポケット（Z軸下側から） ---
# 一文字ホーンがピタッとはまる溝を切り欠く（底面 Z=-24.0 から上に向かってくり抜く）
horn_pocket = Part.makeBox(horn_w, horn_l, horn_depth + 0.5)
horn_pocket.translate(App.Vector(-horn_w / 2.0, -horn_l / 2.0, -24.1))
cut_shapes.append(horn_pocket)

# サーボホーンを底部プレートに固定するための小さなタッピングネジ用下穴（2箇所）
for dy in [-horn_screw_p / 2.0, horn_screw_p / 2.0]:
    h_screw = Part.makeCylinder(
        horn_screw_r,
        6.0,
        App.Vector(0, dy, -24.1),
        App.Vector(0, 0, 1) # Z軸上に貫通させる
    )
    cut_shapes.append(h_screw)

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

print("002_Neck_Joint_Mount.py: ホーン埋込溝を追加した最新マウントが生成されました！")
