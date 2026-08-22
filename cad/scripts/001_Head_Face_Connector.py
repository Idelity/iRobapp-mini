# =========================================================
# File: 001_Head_Face_Connector.py
# Description: iRobapp-mini用 丸型液晶(GC9A01)はめ込み頭部マウント
# Spec: 液晶外径38mm対応 / 底面SG90サーボ(M2穴)ダイレクトマウント仕様
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Head_Case"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
# GC9A01 丸型液晶の標準的な寸法（余裕を持たせたクリアランス込み）
lcd_r       = 19.0    # 液晶基板の半径（外径38mm）
lcd_depth   = 4.0     # 液晶基板とはめ込みに必要な奥行き深さ
wall_t      = 3.0     # 外壁の肉厚 3mm

# SG90サーボ固定用（首のチルト/ピッチ関節との接続用）
servo_screw_pitch = 27.5  # 耳のネジ穴ピッチ
screw_r_m2        = 1.1   # M2ネジ用貫通穴（半径1.1mm）

# 頭部全体のサイズ
head_r = lcd_r + wall_t   # 頭部の外径半径（22mm、直径44mmのコンパクトサイズ）
head_d = 20.0             # 頭部パーツ自体の奥行き（液晶と背面の配線スペースを確保）

# ---------------------------------------------------------
# 1. 頭部ベース形状の作成（コロンとした円柱・コップ状のベース）
# ---------------------------------------------------------
# メインの頭部ソリッド
head_base = Part.makeCylinder(head_r, head_d)

# 底面（サーボと繋ぐ側）にネジ留め用のフラットな「耳」を拡張
ear_block = Part.makeBox(8.0, 36.0, wall_t)
ear_block.translate(App.Vector(-4.0, -18.0, 0)) # 中心を合わせる

main_body = head_base.fuse(ear_block)

# ---------------------------------------------------------
# 2. くり抜き処理（液晶ポケット ＋ 首サーボ接続穴）
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 前面からの液晶はめ込みポケット ---
# 液晶がすっぽり収まるように前面（Z軸の上側）から円柱でくり抜く
lcd_pocket = Part.makeCylinder(lcd_r, lcd_depth + 1.0)
lcd_pocket.translate(App.Vector(0, 0, head_d - lcd_depth))
cut_shapes.append(lcd_pocket)

# 配線（ジャンパ線やFPCケーブル）を後ろに逃がすための中央の四角い貫通穴
wire_hole = Part.makeBox(16.0, 16.0, head_d + 4.0)
wire_hole.translate(App.Vector(-8.0, -8.0, -2.0))
cut_shapes.append(wire_hole)

# --- (B) 底面の首サーボ（SG90）結合用M2ネジ穴（2箇所） ---
for dy in [-servo_screw_pitch / 2.0, servo_screw_pitch / 2.0]:
    s_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 4.0,
        App.Vector(0, dy, -2.0),
        App.Vector(0, 0, 1) # Z軸方向に垂直に貫通
    )
    cut_shapes.append(s_hole)

# ---------------------------------------------------------
# 3. くり抜き実行とドキュメント出力
# ---------------------------------------------------------
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

final_shape = main_body.cut(cutter)

head_part = doc.addObject("Part::Feature", "Head_Face_Connector")
head_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("001_Head_Face_Connector.py: GC9A01液晶対応の頭部ベースが正常に生成されました！")
