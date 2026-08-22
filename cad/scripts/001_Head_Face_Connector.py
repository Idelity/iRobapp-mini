# =========================================================
# File: 001_Head_Face_Connector.py
# Description: iRobapp-mini用 丸型液晶(GC9A01)はめ込み頭部マウント（同軸丸穴仕様）
# Spec: 外径44mm(R22) / 液晶ポケット38mm(R19) / 中央R17穴・底厚3mm / 中央R11丸穴完全貫通仕様
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Head_Case"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（ご指定の極薄・軽量化寸法）
# ---------------------------------------------------------
head_r     = 22.0  # ① 頭部の外径半径：22mm（直径44mm）
lcd_r      = 19.0  # ② 液晶ポケットの半径：19mm（直径38mm）
lcd_depth  = 4.0   # 液晶が収まる深さ：4mm
head_d     = 20.0  # 頭部全体の奥行き：20mm

# ③ ご指定の中穴肉抜き丸穴の半径：17.0mm（直径34.0mm）
inner_wire_r = 17.0 

# ④ ご指定の底面に残す肉厚（床の厚み）：3.0mm
floor_t = 3.0

# 【新設】⑤ 配線と工具がストンと通り抜ける中央の貫通丸穴の半径：11.0mm（直径22.0mm）
center_hole_r = 11.0

# 首（002）と結合するためのM2ネジ穴（2箇所）
screw_r_m2       = 1.1   # M2ネジ用穴（半径1.1mm、直径2.2mm）
head_screw_pitch = 27.5  # Y軸方向のネジピッチ

# ---------------------------------------------------------
# 1. 頭部ベース形状の作成（外径44mmのクリーンな円柱ソリッド）
# ---------------------------------------------------------
main_body = Part.makeCylinder(head_r, head_d)

# ---------------------------------------------------------
# 2. 同軸の「丸」だけでくり抜くステップ処理 
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 前面からの液晶はめ込みポケット（半径19mm、深さ4mm） ---
lcd_pocket = Part.makeCylinder(lcd_r, lcd_depth + 1.0)
lcd_pocket.translate(App.Vector(0.0, 0.0, head_d - lcd_depth))
cut_shapes.append(lcd_pocket)

# --- (B) 中央の大きな肉抜き丸穴（底面から3.0mm残し、半径17mm） ---
center_void = Part.makeCylinder(inner_wire_r, head_d)
center_void.translate(App.Vector(0.0, 0.0, floor_t))
cut_shapes.append(center_void)

# --- (C) 【修正】中央を最後までくり抜く配線用の丸穴（半径11mm） ---
# Z=0から天面までをストンと一気に垂直貫通させる円柱を配置
center_tunnel = Part.makeCylinder(center_hole_r, head_d + 4.0)
center_tunnel.translate(App.Vector(0.0, 0.0, -2.0))
cut_shapes.append(center_tunnel)

# --- (D) 首（002）の天面とドッキングするためのM2ネジ穴（2箇所） ---
for dy in [-head_screw_pitch / 2.0, head_screw_pitch / 2.0]:
    s_hole = Part.makeCylinder(
        screw_r_m2,
        floor_t + 2.0,
        App.Vector(0.0, dy, -1.0),
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(s_hole)

# ---------------------------------------------------------
# 3. くり抜き実行とドキュメント出力
# ---------------------------------------------------------
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

# まっさらな円柱から、すべての丸穴をまとめて一発引き算
final_shape = main_body.cut(cutter)

head_part = doc.addObject("Part::Feature", "Head_Face_Connector")
head_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("001_Head_Face_Connector.py: シンプルな同軸丸穴仕様の頭部ベースが生成されました！")
