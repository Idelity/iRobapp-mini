# =========================================================
# File: 002_Neck_Joint_Mount.py
# Description: iRobapp-mini用 首の上下左右(パン・チルト)関節マウント
# Spec: 厚みすべて3mmのコの字型 / 前面の溝深さを1.5mmに制限し、3つのネジ穴を完全復活
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Neck_Joint"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（001の耳と完全同期）
# ---------------------------------------------------------
wall_t     = 3.0       # すべての板の厚み: 3mm
plate_w    = 8.0       # 001の耳の幅に完全一致: 8.0mm
plate_l_long = 36.0    # 天面・底面プレートの長さ: 36.0mm

# 内側の空間高さ（全高33mm - 天面3mm - 底面3mm = 内寸27mm）
inner_h = 27.0
total_h = inner_h + (wall_t * 2.0) # 全高33.0mm

# 穴あけ用の規格パラメータ
screw_r_m2       = 1.1   # M2ネジ用貫通穴（半径1.1mm、直径2.2mm）
head_screw_pitch = 27.5  # 001番と結合するためのY軸方向のネジピッチ

# SG90付属の一文字ホーン埋め込み用パラメータ（底面・前面共通）
horn_w       = 5.0       # 一文字ホーンの幅
horn_l       = 16.0      # 一文字ホーンの長さ
horn_depth   = 1.5       # ホーンを埋め込む深さ（3mmのうち1.5mmだけを削る！）
horn_screw_p = 11.0      # ホーン固定用ミニネジのピッチ
horn_screw_r = 0.8       # サーボ付属ミニネジ用の下穴

# ---------------------------------------------------------
# 1. コの字型ベース形状の作成（一括切り出し）
# ---------------------------------------------------------
main_block = Part.makeBox(plate_w, plate_l_long, total_h)
main_block.translate(App.Vector(-plate_w / 2.0, -plate_l_long / 2.0, 0.0))

cut_shapes = []

# コの字の内側の空洞を作るための「引き算用ボックス」
inner_void = Part.makeBox(plate_w + 4.0, plate_l_long, inner_h)
inner_void.translate(App.Vector(-(plate_w + 4.0) / 2.0, -plate_l_long / 2.0 + wall_t, wall_t))
cut_shapes.append(inner_void)

# ---------------------------------------------------------
# 2. 追加のくり抜き処理（天面ネジ穴 ＆ 底面サーボホーン3穴 ＆ 前面サーボホーン3穴）
# ---------------------------------------------------------
# --- (A) 上の板（天面）：001と合体するためのM2ネジ穴（2箇所） ---
for dy in [-head_screw_pitch / 2.0, head_screw_pitch / 2.0]:
    t_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 2.0,
        App.Vector(0.0, dy, total_h - wall_t - 1.0),
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(t_hole)

# --- (B) 下の板（底面）：パンサーボのホーンを埋め込むポケット（裏側から） ---
horn_pocket = Part.makeBox(horn_w, horn_l, horn_depth)
horn_pocket.translate(App.Vector(-horn_w / 2.0, -horn_l / 2.0, -0.1))
cut_shapes.append(horn_pocket)

# 下面ネジ穴（3箇所）
center_screw = Part.makeCylinder(screw_r_m2, wall_t + 2.0, App.Vector(0.0, 0.0, -1.0), App.Vector(0, 0, 1))
cut_shapes.append(center_screw)
for dy in [-horn_screw_p / 2.0, horn_screw_p / 2.0]:
    b_screw = Part.makeCylinder(horn_screw_r, wall_t + 2.0, App.Vector(0.0, dy, -1.0), App.Vector(0, 0, 1))
    cut_shapes.append(b_screw)

# --- (C) 【精密修正】前面の縦壁面：深さを1.5mmに制限したホーン溝 ＆ 3つの貫通穴 ---
# 前面の壁面（Y = -18.0mm）に対して、Y軸プラス方向（奥）へ「ジャスト1.5mmだけ」削るボックスを配置。
# 計算エラーを防ぐため、手前の空中（Y=-19.0mm）からスタートして、Y=-16.5mmの位置（壁のちょうど真ん中）でピタッと止めます。
# これにより、3mmの壁の奥半分（1.5mm分）がしっかり残ります！
front_horn_pocket = Part.makeBox(horn_w, horn_depth + 1.0, horn_l)
front_horn_pocket.translate(App.Vector(-horn_w / 2.0, -19.0, 16.5 - horn_l / 2.0))
cut_shapes.append(front_horn_pocket)

# 1. 前面：メイン軸用貫通穴（1箇所）
# 手前の空中（Y=-25.0mm）から奥（Y=0.0mm）まで串刺しにして、残った1.5mmの肉に綺麗な丸穴を開けます。
front_center_screw = Part.makeCylinder(screw_r_m2, 30.0, App.Vector(0.0, -25.0, 16.5), App.Vector(0, 1, 0))
cut_shapes.append(front_center_screw)

# 2. 前面：サーボホーン固定用の上下のネジ穴（2箇所）
for dz in [-horn_screw_p / 2.0, horn_screw_p / 2.0]:
    front_b_screw = Part.makeCylinder(horn_screw_r, 30.0, App.Vector(0.0, -25.0, 16.5 + dz), App.Vector(0, 1, 0))
    cut_shapes.append(front_b_screw)

# ---------------------------------------------------------
# 3. くり抜き実行とドキュメント出力
# ---------------------------------------------------------
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

final_shape = main_block.cut(cutter)

neck_part = doc.addObject("Part::Feature", "Neck_Joint_Mount")
neck_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("002_Neck_Joint_Mount.py: 溝の深さを適正化し、3つの穴が美しく復活しました！")
