# =========================================================
# File: 001_Head_Face_Connector.py
# Description: iRobapp-mini用 丸型液晶はめ込み頭部マウント（手前・奥Wリブ仕様）
# Spec: 元の寸法100%維持 / 中央R11完全貫通 / 右真横の同じ位置に手前(Z=11)と奥(Z=5)の2基のリブを実装
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Head_Case"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（元の寸法を100%そのまま使用）
# ---------------------------------------------------------
head_r     = 22.0  # ① 頭部の外径半径：22mm（直径44mm）
lcd_r      = 19.0  # ② 液晶ポケットの半径：19mm（直径38mm）
lcd_depth  = 4.0   # 液晶が収まる深さ：4mm
head_d     = 20.0  # 頭部全体の奥行き：20mm

inner_wire_r = 17.0 # ③ 中穴肉抜き丸穴の半径：17.0mm（直径34.0mm）
floor_t = 3.0       # ④ 底面に残す肉厚（床の厚み）：3.0mm
center_hole_r = 11.0 # ⑤ 中央の貫通丸穴の半径：11.0mm（直径22.0mm）

# 首（002）と結合するためのM2ネジ穴
screw_r_m2       = 1.1   # M2ネジ用穴（半径1.1mm）
head_screw_pitch = 27.5  # Y軸方向のネジピッチ

# ---------------------------------------------------------
# 1. 頭部ベース形状の作成（外径44mmのクリーンな円柱ソリッド）
# ---------------------------------------------------------
main_body = Part.makeCylinder(head_r, head_d)

# ---------------------------------------------------------
# 2. 元の同軸「丸」だけでくり抜くステップ処理
# ---------------------------------------------------------
# 前面からの液晶はめ込みポケット（深さ4mm）
lcd_pocket = Part.makeCylinder(lcd_r, lcd_depth + 1.0)
lcd_pocket.translate(App.Vector(0.0, 0.0, head_d - lcd_depth))

# 中央の大きな肉抜き丸穴（底面から 3.0mm の床を残す）
center_void = Part.makeCylinder(inner_wire_r, head_d)
center_void.translate(App.Vector(0.0, 0.0, floor_t))

# 中央を最後までくり抜く配線用の丸穴（半径11mm完全貫通）
center_tunnel = Part.makeCylinder(center_hole_r, head_d + 4.0)
center_tunnel.translate(App.Vector(0.0, 0.0, -2.0))

# ドッキング用M2ネジ穴（ネジが短くて済む、床厚3.0mm+2.0mmの浅型仕様）
s_hole1 = Part.makeCylinder(screw_r_m2, floor_t + 2.0, App.Vector(0.0, -head_screw_pitch / 2.0, -1.0), App.Vector(0, 0, 1))
s_hole2 = Part.makeCylinder(screw_r_m2, floor_t + 2.0, App.Vector(0.0, head_screw_pitch / 2.0, -1.0), App.Vector(0, 0, 1))

# 一括で結合してベースからくり抜く
cutter = lcd_pocket.fuse(center_void).fuse(center_tunnel).fuse(s_hole1).fuse(s_hole2)
base_head = main_body.cut(cutter)

# ---------------------------------------------------------
# 3. 床（板）の上にアンプ用と【修正】手前・奥のWスピーカー削り切りリブを追加
# ---------------------------------------------------------
add_shapes = []

# --- MAX98357A アンプ挟み込み用リブ（左側の奥の床に配置 / 高さ5mm） ---
amp_rib_h = 5.0
amp_rib_w = 2.0
amp_rib_t = 2.0
amp_rib1 = Part.makeBox(amp_rib_w, amp_rib_t, amp_rib_h)
amp_rib1.translate(App.Vector(-13.0, 10.0, floor_t)) # X = -13mm, Y = 10mm
amp_rib2 = Part.makeBox(amp_rib_w, amp_rib_t, amp_rib_h)
amp_rib2.translate(App.Vector(-13.0, -12.0, floor_t)) # X = -13mm, Y = -12mm（隙間20mm）
add_shapes.append(amp_rib1)
add_shapes.append(amp_rib2)

# --- 27mmスピーカー用 5mm×5mm×5mm 削り切りリブの形状定義 ---
spk_rib_size = 5.0
groove_w = 5.5
groove_t = 2.5
groove_d = 6.0

def create_shaved_rib():
    solid = Part.makeBox(spk_rib_size, spk_rib_size, spk_rib_size)
    groove = Part.makeBox(groove_w, groove_d, groove_t)
    groove.translate(App.Vector(-0.2, -0.5, spk_rib_size - groove_t))
    return solid.cut(groove)

# 【1基目：手前側リブ】位置はそのままキープ（液晶のすぐ裏 Z = 11.0mm に配置）
shaved_spk_rib_front = create_shaved_rib()
shaved_spk_rib_front.translate(App.Vector(12.0, -spk_rib_size / 2.0, 11.0))
add_shapes.append(shaved_spk_rib_front)

# 【2基目：奥側リブ】全く同じ大きさのものを、すぐ真ろ（Z = 5.0mm の奥側）に追加！
# XとYの平面上の位置（右側面中央）は完璧に同じで、奥行き（Z軸方向）だけをずらして2階建てに配置
shaved_spk_rib_back = create_shaved_rib()
shaved_spk_rib_back.translate(App.Vector(12.0, -spk_rib_size / 2.0, 5.0))
add_shapes.append(shaved_spk_rib_back)

# 各リブを元の土台にダイレクトに一体化（fuse）させる
final_shape = base_head.fuse(amp_rib1).fuse(amp_rib2).fuse(shaved_spk_rib_front).fuse(shaved_spk_rib_back)

# ---------------------------------------------------------
# 4. ドキュメントへの出力
# ---------------------------------------------------------
head_part = doc.addObject("Part::Feature", "Head_Face_Connector")
head_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("001_Head_Face_Connector.py: 手前と奥のWリブ構造により、前後のグラつきを完璧に抑える仕様が確定しました！")
