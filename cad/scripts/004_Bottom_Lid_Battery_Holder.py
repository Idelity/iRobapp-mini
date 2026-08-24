# =========================================================
# File: 004_Bottom_Lid_Battery_Holder.py
# Description: iRobapp-mini用 電源系底蓋（スイッチ貫通構造修正版）
# Spec: 底面からスイッチのつまみを直接操作できる貫通スリット仕様
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Bottom_Lid"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
wall_t = 3.0           # 基本の肉厚 3mm
lid_clearance = 0.4    # クリアランス

# 底蓋の半径（約31.6mm、直径約63.2mm）
body_r = 35.0          
lid_r  = body_r - wall_t - lid_clearance  

# 1. バッテリー（DTP502535）用ホルダー設定
batt_w = 26.0          
batt_h = 8.0           
rib_thick = 2.0        
rib_length = 30.0      

# 2. ヒューズ（MF-R090）用ポケット設定
fuse_w = 12.2          
fuse_t = 3.6           
fuse_h = 10.0          
wall_f = 1.5           

# 3. スイッチ（SS-12D00G）用ホルダー設定
sw_w = 9.1            # スイッチ本体が入る内幅
sw_t = 4.0            # スイッチ本体が入る内厚
sw_h = 7.0            # ホルダー壁の高さ
wall_s = 1.5          # ホルダーの肉厚

slot_w = 4.5          # つまみが動くスリット幅
slot_t = 2.5          # つまみの厚み

# ---------------------------------------------------------
# 1. 底蓋ベース円盤の作成
# ---------------------------------------------------------
lid_base = Part.makeCylinder(lid_r, 2.0)

# ---------------------------------------------------------
# 2. バッテリー固定リブの作成
# ---------------------------------------------------------
rib1 = Part.makeBox(rib_length, rib_thick, batt_h)
rib1.translate(App.Vector(-rib_length / 2.0, (batt_w / 2.0), 2.0))

rib2 = Part.makeBox(rib_length, rib_thick, batt_h)
rib2.translate(App.Vector(-rib_length / 2.0, -(batt_w / 2.0) - rib_thick, 2.0))

# ---------------------------------------------------------
# 3. ヒューズホルダー（ポケット）の作成
# ---------------------------------------------------------
fuse_outer = Part.makeBox(fuse_w + (wall_f * 2), fuse_t + (wall_f * 2), fuse_h)
fuse_inner = Part.makeBox(fuse_w, fuse_t, fuse_h + 1.0)
fuse_inner.translate(App.Vector(wall_f, wall_f, 0.0))
fuse_pocket = fuse_outer.cut(fuse_inner)
fuse_pocket.translate(App.Vector(- (fuse_w + wall_f * 2) / 2.0, 16.0, 2.0))

# ---------------------------------------------------------
# 4. 【修正】スライドスイッチホルダー ＆ 貫通穴の作成
# ---------------------------------------------------------
# スイッチをホールドする外枠（底が抜けている筒状の壁）
sw_wall_outer = Part.makeBox(sw_w + (wall_s * 2), sw_t + (wall_s * 2), sw_h)
sw_wall_inner = Part.makeBox(sw_w, sw_t, sw_h + 1.0)
sw_wall_inner.translate(App.Vector(wall_s, wall_s, -0.5))
sw_holder_wall = sw_wall_outer.cut(sw_wall_inner)

# スイッチの配置予定座標（Y軸マイナス側）
sw_pos_x = - (sw_w + wall_s * 2) / 2.0
sw_pos_y = -22.0
sw_holder_wall.translate(App.Vector(sw_pos_x, sw_pos_y, 2.0))

# ベース円盤（lid_base）を「完全に貫通」するつまみ用のスリット穴を作成
# 位置はホルダーの内側の中心にピッタリ合わせます
final_slot = Part.makeBox(slot_w, slot_t, 5.0)
final_slot.translate(App.Vector(
    sw_pos_x + wall_s + (sw_w - slot_w) / 2.0, 
    sw_pos_y + wall_s + (sw_t - slot_t) / 2.0, 
    -1.0
))

# ---------------------------------------------------------
# 5. 結合とくり抜きの最終処理
# ---------------------------------------------------------
# 先にベース円盤とすべての「壁（リブ）」を合体させる
combined_body = lid_base.fuse(rib1).fuse(rib2).fuse(fuse_pocket).fuse(sw_holder_wall)

# 合体させた全体に対して、つまみ用の貫通穴（final_slot）を一気にぶち抜く！
final_shape = combined_body.cut(final_slot)

# ドキュメントへの出力
lid_part = doc.addObject("Part::Feature", "Bottom_Lid_Battery_Holder")
lid_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("004_Bottom_Lid_Battery_Holder.py: データが生成されました！")
