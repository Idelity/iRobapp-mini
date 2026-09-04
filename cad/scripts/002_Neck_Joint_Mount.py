# =========================================================
# File: 002_Neck_Joint_Mount.py
# Description: iRobapp-mini用 首の上下左右(パン・チルト)関節マウント
# Spec: L字型 / パーツ幅8.0mm固定 / 前面: サーボホーン溝 / 底面: 頭部結合用M2×2穴
# Update: 底面のネジピッチを28.0mmに変更、ネジ穴を後ろ側に2mm微調整（行き過ぎを修正）
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Neck_Joint_Mount"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定
# ---------------------------------------------------------
wall_t     = 3.0       # すべての板の厚み: 3mm
plate_w    = 8.0       # 【ご要望】パーツの幅を8.0mmに完全固定
plate_l_long = 36.0    # 底面プレートの長さ: 36.0mm

# 内側の空間高さ（全高30mm - 底面3mm = 内寸27mm）
inner_h = 27.0
total_h = inner_h + wall_t # 全高30.0mm

# 穴あけ用の規格パラメータ
screw_r_m2       = 1.1   # M2ネジ用貫通穴（半径1.1mm）
head_joint_pitch = 28.0  # 【変更】頭部部品と結合するネジ穴の間隔: 28.0mm
head_hole_offset = 2.0   # 【微調整】後ろ側へのずらす量を2.0mmに変更

# --- SG90最小ホーン（前面用・クリアランス込み） ---
horn_w       = 8.0       # パーツ幅8mmと同じ（幅いっぱいの溝になります）
horn_l       = 20.0 + 1.0 # クリアランス込みの長さ（21.0mm）
horn_depth   = 1.5 + 0.2  # 印刷のダレを考慮し、深さを1.7mmに調整
horn_screw_p = 11.0       # ホーン固定用ミニネジのピッチ
horn_screw_r = 0.8        # サーボ付属ミニネジ用の下穴

# ---------------------------------------------------------
# 1. L字型ベース形状の作成（一括切り出し）
# ---------------------------------------------------------
main_block = Part.makeBox(plate_w, plate_l_long, total_h)
main_block.translate(App.Vector(-plate_w / 2.0, -plate_l_long / 2.0, 0.0))

cut_shapes = []

# 【L字型カット】前面の壁（厚み3mm）だけ残して、後ろ側をすべて削る巨大ボックス
l_shape_void = Part.makeBox(plate_w + 4.0, plate_l_long, total_h + 2.0)
l_shape_void.translate(App.Vector(-(plate_w + 4.0) / 2.0, -plate_l_long / 2.0 + wall_t, wall_t))
cut_shapes.append(l_shape_void)

# ---------------------------------------------------------
# 2. 追加のくり抜き処理（底面：頭部結合2穴 ＆ 前面：サーボホーン溝・3穴）
# ---------------------------------------------------------
# --- (A) 底面（水平板）：頭部部品と結合するM2ネジ穴（2箇所、ピッチ28mm、後方にオフセット） ---
for dy in [-head_joint_pitch / 2.0, head_joint_pitch / 2.0]:
    head_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 2.0,
        App.Vector(0.0, dy + head_hole_offset, -1.0), # 2.0mmのオフセットを適用
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(head_hole)

# --- (B) 前面（垂直壁面）：サーボホーンを埋め込むポケット ＆ 3つの貫通穴 ---
z_center = total_h / 2.0  # 縦壁の中心高さ

# 前面の溝（Y=-18.0mmの壁面から奥へ1.7mm削る、幅は8.0mmいっぱいでスリット状になります）
front_horn_pocket = Part.makeBox(horn_w + 2.0, horn_depth + 1.0, horn_l)
front_horn_pocket.translate(App.Vector(-(horn_w + 2.0) / 2.0, -19.0, z_center - horn_l / 2.0))
cut_shapes.append(front_horn_pocket)

# 1. 前面：メイン軸用貫通穴（1箇所・M2）
front_center_screw = Part.makeCylinder(screw_r_m2, 30.0, App.Vector(0.0, -25.0, z_center), App.Vector(0, 1, 0))
cut_shapes.append(front_center_screw)

# 2. 前面：サーボホーン固定用の上下のネジ穴（2箇所・ミニネジ用）
for dz in [-horn_screw_p / 2.0, horn_screw_p / 2.0]:
    front_b_screw = Part.makeCylinder(horn_screw_r, 30.0, App.Vector(0.0, -25.0, z_center + dz), App.Vector(0, 1, 0))
    cut_shapes.append(front_b_screw)

# ---------------------------------------------------------
# 3. くり抜き実行とドキュメント出力
# ---------------------------------------------------------
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

# メインブロックから、L字空間・底面ネジ穴・前面ホーン溝を一気に削り出す
final_shape = main_block.cut(cutter)

neck_part = doc.addObject("Part::Feature", "Neck_Joint_Mount")
neck_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("002_Neck_Joint_Mount.py: 出力しました。")
