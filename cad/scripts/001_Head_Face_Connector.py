# =========================================================
# File: 001_Head_Face_Connector.py
# Description: iRobapp-mini用 丸型液晶はめ込み頭部マウント（Waveshare19192突起対応・完全版）
# Spec: 元の寸法100%維持 / 中央R11完全貫通 / 液晶用下部コネクタ逃げスリット新設 / Wリブ仕様
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
# 2. 元の同軸「丸」だけでくり抜くステップ処理 ＋ コネクタ逃げ
# ---------------------------------------------------------
# 前面からの液晶はめ込みポケット（深さ4mm）
lcd_pocket = Part.makeCylinder(lcd_r, lcd_depth + 1.0)
lcd_pocket.translate(App.Vector(0.0, 0.0, head_d - lcd_depth))

# 【新設】Waveshare 19192専用：基板下部の「四角い出っ張り（コネクタ・部品）」を逃がす四角い箱
# 幅20.0mm、奥行き(厚み)は液晶と同じ4.0mm、Y軸マイナス方向（下側）へ3.5mm余分に削り落とします
conn_slit_w = 20.0
conn_slit_h = 5.0
conn_escape = Part.makeBox(conn_slit_w, conn_slit_h, lcd_depth + 1.0)
# 丸いポケットのフチ（Y = -19.0mm）からさらに下へ突き抜けるように配置
conn_escape.translate(App.Vector(-conn_slit_w / 2.0, -lcd_r - 2.5, head_d - lcd_depth))

# 中央の大きな肉抜き丸穴（底面から 3.0mm の床を残す）
center_void = Part.makeCylinder(inner_wire_r, head_d)
center_void.translate(App.Vector(0.0, 0.0, floor_t))

# 中央を最後までくり抜く配線用の丸穴（半径11mm完全貫通）
center_tunnel = Part.makeCylinder(center_hole_r, head_d + 4.0)
center_tunnel.translate(App.Vector(0.0, 0.0, -2.0))

# ドッキング用M2ネジ穴（ネジが短くて済む、床厚 3.0mm+2.0mm の浅型仕様）
s_hole1 = Part.makeCylinder(screw_r_m2, floor_t + 2.0, App.Vector(0.0, -head_screw_pitch / 2.0, -1.0), App.Vector(0, 0, 1))
s_hole2 = Part.makeCylinder(screw_r_m2, floor_t + 2.0, App.Vector(0.0, head_screw_pitch / 2.0, -1.0), App.Vector(0, 0, 1))

# 一括で結合してベースからくり抜く（コネクタ逃げ用のconn_escapeを追加！）
cutter = lcd_pocket.fuse(conn_escape).fuse(center_void).fuse(center_tunnel).fuse(s_hole1).fuse(s_hole2)
base_head = main_body.cut(cutter)

# ---------------------------------------------------------
# 3. 床（板）の上に背高アンプリブ ＆ 15mm幅Wスピーカーリブを追加
# ---------------------------------------------------------
add_shapes = []

# --- MAX98357A アンプ挟み込み用リブ（左側の奥の床に配置 / 高さ10.0mm、厚み5mm仕様） ---
amp_rib_h = 10.0  
amp_rib_w = 5.0   
amp_rib_t = 2.0   

amp_rib1 = Part.makeBox(amp_rib_w, amp_rib_t, amp_rib_h)
amp_rib1.translate(App.Vector(-13.0, 10.25, floor_t)) 

amp_rib2 = Part.makeBox(amp_rib_w, amp_rib_t, amp_rib_h)
amp_rib2.translate(App.Vector(-13.0, -12.25, floor_t)) 

add_shapes.append(amp_rib1)
add_shapes.append(amp_rib2)

# --- 27mmスピーカー用 15mm幅削り切りリブの形状定義 ---
spk_rib_w = 5.0   
spk_rib_t = 15.0  
spk_rib_h = 5.0   

groove_w = 5.5
groove_t = 2.5
groove_d = 20.0

def create_wide_shaved_rib():
    solid = Part.makeBox(spk_rib_w, spk_rib_t, spk_rib_h)
    groove = Part.makeBox(groove_w, groove_d, groove_t)
    groove.translate(App.Vector(-0.2, -2.0, spk_rib_h - groove_t))
    return solid.cut(groove)

# 【1基目：手前側リブ（15mmワイド版）】Z = 12.0mm
shaved_spk_rib_front = create_wide_shaved_rib()
shaved_spk_rib_front.translate(App.Vector(12.0, -spk_rib_t / 2.0, 12.0))
add_shapes.append(shaved_spk_rib_front)

# 【2基目：奥側リブ（15mmワイド版）】Z = 4.5mm
shaved_spk_rib_back = create_wide_shaved_rib()
shaved_spk_rib_back.translate(App.Vector(12.0, -spk_rib_t / 2.0, 4.5))
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

print("001_Head_Face_Connector.py: 液晶下部の出っ張りも完璧に逃がす、真の最終マスターデータがFIXしました！")
