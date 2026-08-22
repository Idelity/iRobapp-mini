# =========================================================
# File: 003_Body_Base_Case.py
# Description: iRobapp-mini用 デスクトップ土台（メカ・電子部品内蔵ボディ）
# Spec: 首・尻尾サーボ適合 / XIAO給電用USB穴 / 背面スイッチ・ヒューズ穴 / 【修正】完全に独立した右側配線大穴仕様
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Body_Base"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定（mm単位）
# ---------------------------------------------------------
screw_r_m2 = 1.1       # M2ネジ用穴（半径1.1mm）
wall_t     = 3.0       # 外壁の肉厚 3mm

# 首ジョイント（002）側から繋がるSG90サーボの耳ピッチ
head_screw_pitch = 27.5

# 土台（ボディ）の全体サイズ
body_r = 35.0          # 土台の底面半径（直径70mmの安定感ある卓上サイズ）
body_h = 40.0          # 土台の高さ（4cmの高さに電子部品を凝縮）

# 背面パーツ用のくり抜き寸法（標準的な小型ロッカースイッチ＆ヒューズホルダー想定）
switch_w = 12.0        # スイッチ取付穴の幅
switch_h = 19.0        # スイッチ取付穴の高さ
fuse_r   = 6.0         # パネルマウント型ヒューズホルダーの穴半径（直径12mm）

# XIAO ESP32-S3 マイコンのUSB-Cポートアクセス穴の寸法
usb_w = 11.0           # USB-Cケーブルのプラプラグが干渉しない幅
usb_h = 6.5            # USB-Cプラグの厚み＋余裕

# SG90尻尾サーボ用の標準寸法
tail_servo_w = 23.0    # 尻尾サーボ本体の横幅
tail_servo_h = 12.4    # 尻尾サーボ本体の縦幅
tail_servo_pitch = 27.5 # ネジのピッチ

# 天面の配線専用大穴の半径：5.0mm（直径10.0mm）
wire_hole_r = 5.0

# ---------------------------------------------------------
# 1. ボディベース形状の作成（スマートなテーパー付き円柱）
# ---------------------------------------------------------
body_solid = Part.makeCone(body_r, body_r - 7.0, body_h)

# ---------------------------------------------------------
# 2. くり抜き処理（内蔵スペース ＋ 各種加工窓 ＋ 独立した配線大穴）
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 内部の電子部品収納スペース（インナーポケット） ---
inner_space = Part.makeCone(body_r - wall_t, body_r - 7.0 - wall_t, body_h - wall_t)
cut_shapes.append(inner_space)

# --- (B) 天面：首振り用SG90サーボを落とし込むスリットとネジ穴（Z軸貫通） ---
servo_hole = Part.makeBox(13.4, 23.4, wall_t + 4.0)
servo_hole.translate(App.Vector(-13.4 / 2.0, -23.4 / 2.0, body_h - wall_t - 2.0))
cut_shapes.append(servo_hole)

for dy in [-head_screw_pitch / 2.0, head_screw_pitch / 2.0]:
    s_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 4.0,
        App.Vector(0, dy, body_h - wall_t - 2.0),
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(s_hole)

# --- (C) 【プラン①適用】天面：サーボ用四角穴から完全に「独立」させた配線大穴 ---
# ご指示通りさらに右（X = 14.5mm）へ離したことで、サーボの四角穴（X最大6.7mm）のフチとぶつからず、
# 1本の綺麗な真ん丸の貫通穴として独立して削り出されます。ネジ穴の保護も完璧です。
top_wire_hole = Part.makeCylinder(
    wire_hole_r,
    55.0,
    App.Vector(14.5, 9.0, 50.0),
    App.Vector(0, 0, -1) # Z軸マイナス方向に垂直貫通
)
cut_shapes.append(top_wire_hole)

# --- (D) 背面：電源スイッチ穴（Y軸方向貫通の四角穴） ---
switch_hole = Part.makeBox(switch_w, wall_t + 10.0, switch_h)
switch_hole.translate(App.Vector(-switch_w / 2.0, -body_r - 5.0, 6.0))
cut_shapes.append(switch_hole)

# --- (E) 背面：安全のためのヒューズホルダー穴（Y軸方向貫通の丸穴） ---
fuse_hole = Part.makeCylinder(
    fuse_r,
    wall_t + 10.0,
    App.Vector(18.0, -body_r - 5.0, 15.5),
    App.Vector(0, 1, 0)
)
cut_shapes.append(fuse_hole)

# --- (F) 背面/側面：XIAOマイコン用USB-Cアクセス窓 ---
usb_hole = Part.makeBox(usb_w, wall_t + 10.0, usb_h)
usb_hole.translate(App.Vector(-18.0, -body_r - 5.0, 10.0))
cut_shapes.append(usb_hole)

# --- (G) 背面：尻尾フリフリ用サーボを埋め込む窓 ＆ ネジ穴 ---
tail_hole = Part.makeBox(tail_servo_w, 15.0, tail_servo_h)
tail_hole.translate(App.Vector(-tail_servo_w / 2.0, -body_r - 5.0, 24.0))
cut_shapes.append(tail_hole)

for dx in [-tail_servo_pitch / 2.0, tail_servo_pitch / 2.0]:
    t_screw = Part.makeCylinder(
        screw_r_m2,
        15.0,
        App.Vector(dx, -body_r - 5.0, 30.2), 
        App.Vector(0, 1, 0)
    )
    cut_shapes.append(t_screw)

# ---------------------------------------------------------
# 3. くり抜き実行とドキュメント出力
# ---------------------------------------------------------
cutter = cut_shapes
for s in cut_shapes[1:]:
    cutter = cutter.fuse(s)

final_shape = body_solid.cut(cutter)

body_part = doc.addObject("Part::Feature", "Body_Base_Case")
body_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("003_Body_Base_Case.py: 丸穴を完全に独立させた、美しい最終デザインの土台が完成しました！")
