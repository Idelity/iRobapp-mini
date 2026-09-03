# =========================================================
# File: 004_Bottom_Lid_Battery_Holder.py
# Description: iRobapp-mini用 電源系底蓋（4つ角ネジ穴・完全貫通版）
# Spec: ボディケース（50x60、内寸44x54）に完全適合する長方形蓋（クリアランス込）
#       バッテリーリブ間隔24.5mm / リブの長さを10.0mmに短縮
#       奥側にヒューズとスイッチを横並び配置（干渉回避） / 全高を「7.0mm」に統一
#       【修正】バグを解消し、4つ角にM2固定ネジ穴を確実に貫通！
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Bottom_Lid_Battery_Holder"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
screw_r_m2 = 1.1       # M2ネジ用穴（半径1.1mm）
wall_t = 3.0           # 基本の肉厚 3mm
lid_clearance = 0.4    # 3D印刷時の着脱用クリアランス

# 長方形ボディケースの内寸（幅44.0mm、長さ54.0mm）に合わせた蓋サイズ
lid_w = (50.0 - wall_t * 2.0) - (lid_clearance * 2.0)  # 43.2mm
lid_l = (60.0 - wall_t * 2.0) - (lid_clearance * 2.0)  # 53.2mm
lid_h = 2.0                                            # 蓋のベース厚み 2mm

# 高さ共通化（7.0mm統一）
common_h = 7.0

# 1. バッテリー用ホルダー設定
batt_w = 26.0 - 1.5    # 24.5mm
batt_h = common_h
rib_thick = 2.0
rib_length = 10.0

# 2. ヒューズ（MF-R090）用ポケット設定
fuse_w = 12.2
fuse_t = 3.6
fuse_h = common_h
wall_f = 1.5

# 3. スイッチ（SS-12D00G）用ホルダー設定
sw_w = 9.1
sw_t = 4.0
sw_h = common_h
wall_s = 1.5

slot_w = 4.5
slot_t = 2.5

# ---------------------------------------------------------
# 1. 底蓋ベース長方形の作成
# ---------------------------------------------------------
lid_base = Part.makeBox(lid_w, lid_l, lid_h)
lid_base.translate(App.Vector(-lid_w / 2.0, -lid_l / 2.0, 0.0))

# ---------------------------------------------------------
# 2. バッテリー固定リブの作成
# ---------------------------------------------------------
rib1 = Part.makeBox(rib_length, rib_thick, batt_h)
rib1.translate(App.Vector(-rib_length / 2.0, (batt_w / 2.0), lid_h))

rib2 = Part.makeBox(rib_length, rib_thick, batt_h)
rib2.translate(App.Vector(-rib_length / 2.0, -(batt_w / 2.0) - rib_thick, lid_h))

# ---------------------------------------------------------
# 3. ヒューズホルダー（ポケット）の作成
# ---------------------------------------------------------
fuse_outer = Part.makeBox(fuse_w + (wall_f * 2), fuse_t + (wall_f * 2), fuse_h)
fuse_inner = Part.makeBox(fuse_w, fuse_t, fuse_h + 1.0)
fuse_inner.translate(App.Vector(wall_f, wall_f, -0.5))
fuse_pocket = fuse_outer.cut(fuse_inner)

fuse_pocket.translate(App.Vector(-10.0 - (fuse_w + wall_f * 2) / 2.0, 14.0, lid_h))

# ---------------------------------------------------------
# 4. スライドスイッチホルダー ＆ 貫通穴の作成
# ---------------------------------------------------------
sw_wall_outer = Part.makeBox(sw_w + (wall_s * 2), sw_t + (wall_s * 2), sw_h)
sw_wall_inner = Part.makeBox(sw_w, sw_t, sw_h + 1.0)
sw_wall_inner.translate(App.Vector(wall_s, wall_s, -0.5))
sw_holder_wall = sw_wall_outer.cut(sw_wall_inner)

sw_pos_x = 12.0 - (sw_w + wall_s * 2) / 2.0
sw_pos_y = 14.0
sw_holder_wall.translate(App.Vector(sw_pos_x, sw_pos_y, lid_h))

# ---------------------------------------------------------
# 5. くり抜き穴のリスト作成（スイッチスリット ＆ 4つ角ネジ穴）
# ---------------------------------------------------------
cut_shapes = []

# A. スライドスイッチつまみ用のスリット穴
final_slot = Part.makeBox(slot_w, slot_t, lid_h + 4.0)
final_slot.translate(App.Vector(
    sw_pos_x + wall_s + (sw_w - slot_w) / 2.0,
    sw_pos_y + wall_s + (sw_t - slot_t) / 2.0,
    -1.0
))
cut_shapes.append(final_slot)

# B. 4つ角のネジ固定穴（4箇所）
# ボディ（50mm×60mm、肉厚3mm）のリブの中心に完全に連動させます
screw_offset_x = (50.0 / 2.0 - wall_t) - 2.0  # 20.0mm
screw_offset_y = (60.0 / 2.0 - wall_t) - 2.0  # 25.0mm

for sx in [-1, 1]:
    for sy in [-1, 1]:
        corner_screw = Part.makeCylinder(
            screw_r_m2,
            lid_h + 4.0,
            App.Vector(screw_offset_x * sx, screw_offset_y * sy, -1.0),
            App.Vector(0, 0, 1)
        )
        cut_shapes.append(corner_screw)

# ---------------------------------------------------------
# 6. 結合とくり抜きの最終処理（バグ修正箇所）
# ---------------------------------------------------------
# ベース長方形とすべての突起パーツ（リブ・ホルダー）を合体
combined_body = lid_base.fuse(rib1).fuse(rib2).fuse(fuse_pocket).fuse(sw_holder_wall)

# 【バグ修正】リストの最初の要素（要素0）で初期化し、それ以降を安全にfuseする
cutter = cut_shapes[0]
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

# 合体した全体から、完成したくり抜き用マスター（cutter）を一気に差し引く
final_shape = combined_body.cut(cutter)

# ドキュメントへの出力
lid_part = doc.addObject("Part::Feature", "Bottom_Lid_Battery_Holder")
lid_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("004_Bottom_Lid_Battery_Holder.py: 出力しました。")
