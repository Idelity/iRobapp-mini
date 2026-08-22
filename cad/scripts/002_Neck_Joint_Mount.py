# =========================================================
# File: 002_Neck_Joint_Mount.py
# Description: iRobapp-mini用 首の上下左右(パン・チルト)関節マウント
# Spec: 厚みすべて3mmのコの字型 / 天面2穴 / 底面サーボホーン結合（3穴仕様）
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Neck_Joint"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（共通・規格寸法）
# ---------------------------------------------------------
wall_t     = 3.0       # すべての板の厚み: 3mm
plate_w    = 20.0      # すべての板の共通の幅: 20mm
plate_l_long = 36.0    # 天面・底面プレートの長さ: 36mm

# 内側の空間高さ（全高33mm - 天面3mm - 底面3mm = 内寸27mm、これで縦壁が30mmになります）
inner_h = 27.0
total_h = inner_h + (wall_t * 2.0) # 全高33.0mm

# 穴あけ用の規格パラメータ
screw_r_m2       = 1.1   # M2ネジ用貫通穴（半径1.1mm、直径2.2mm）
head_screw_pitch = 27.5  # 001番と結合するためのY軸方向のネジピッチ

# SG90付属の一文字ホーン埋め込み用パラメータ（底面用）
horn_w       = 5.0       # 一文字ホーンの幅
horn_l       = 16.0      # 一文字ホーンの長さ
horn_depth   = 1.5       # ホーンを埋め込む深さ（底面3mmのうち1.5mmを削る）
horn_screw_p = 11.0      # ホーン固定用ミニネジのピッチ（中心から左右5.5mm）
horn_screw_r = 0.8       # サーボ付属ミニネジ用の下穴（半径0.8mm）

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
# 2. 追加のくり抜き処理（天面ネジ穴 ＆ 底面サーボホーン3穴）
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

# 【修正】1. サーボの回転軸と直接繋ぐ「中心のメイン貫通穴」（1箇所）
# サーボ付属のメインビスがストンと通るように、原点(0,0)の位置を垂直に貫通させます
center_screw = Part.makeCylinder(
    screw_r_m2,
    wall_t + 2.0,
    App.Vector(0.0, 0.0, -1.0),
    App.Vector(0, 0, 1)
)
cut_shapes.append(center_screw)

# 2. サーボホーンのプラスチックの羽を固定するための両サイドのネジ穴（2箇所）
for dy in [-horn_screw_p / 2.0, horn_screw_p / 2.0]:
    b_screw = Part.makeCylinder(
        horn_screw_r,
        wall_t + 2.0,
        App.Vector(0.0, dy, -1.0),
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(b_screw)

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

print("002_Neck_Joint_Mount.py: 底面にメイン軸ネジを含む3穴を開けた完全版が生成されました！")
