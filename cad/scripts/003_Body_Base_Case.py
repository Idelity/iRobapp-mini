# =========================================================
# File: 003_Body_Base_Case.py
# Description: iRobapp-mini用 デスクトップ土台（メカ・電子部品内蔵ボディ）
# Spec: 首サーボ適合 / XIAO給電用USB穴 / 背面スイッチ・ヒューズ穴
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

# ---------------------------------------------------------
# 1. ボディベース形状の作成（スマートなテーパー付き円柱）
# ---------------------------------------------------------
# 机の上で安定し、上に向かって少し絞られる綺麗な円錐台（コーン形状）を作ります
# 下面半径 35mm、上面半径 28mm、高さ 40mm
body_solid = Part.makeCone(body_r, body_r - 7.0, body_h)

# ---------------------------------------------------------
# 2. くり抜き処理（内蔵スペース ＋ サーボ固定穴 ＋ スイッチ類 ＋ USB窓）
# ---------------------------------------------------------
cut_shapes = []

# --- (A) 内部の電子部品収納スペース（インナーポケット） ---
# 肉厚3mmを残して、下側から中をまるごとくり抜きます
inner_space = Part.makeCone(body_r - wall_t, body_r - 7.0 - wall_t, body_h - wall_t)
cut_shapes.append(inner_space)

# --- (B) 天面：首振り用SG90サーボを落とし込むスリットとネジ穴（Z軸貫通） ---
# サーボ本体が通る長方形の穴
servo_hole = Part.makeBox(13.4, 23.4, wall_t + 4.0)
servo_hole.translate(App.Vector(-13.4 / 2.0, -23.4 / 2.0, body_h - wall_t - 2.0))
cut_shapes.append(servo_hole)

# サーボの耳を固定するM2ネジ穴（2箇所）
for dy in [-head_screw_pitch / 2.0, head_screw_pitch / 2.0]:
    s_hole = Part.makeCylinder(
        screw_r_m2,
        wall_t + 4.0,
        App.Vector(0, dy, body_h - wall_t - 2.0),
        App.Vector(0, 0, 1)
    )
    cut_shapes.append(s_hole)

# --- (C) 背面：電源スイッチ穴（Y軸方向貫通の四角穴） ---
# 土台の後ろ側（Y軸マイナス方向の壁）にスイッチを配置
switch_hole = Part.makeBox(switch_w, wall_t + 10.0, switch_h)
switch_hole.translate(App.Vector(-switch_w / 2.0, -body_r - 5.0, 8.0))
cut_shapes.append(switch_hole)

# --- (D) 背面：安全のためのヒューズホルダー穴（Y軸方向貫通の丸穴） ---
# スイッチの横（X軸プラス方向にずらした位置）に配置
fuse_hole = Part.makeCylinder(
    fuse_r,
    wall_t + 10.0,
    App.Vector(18.0, -body_r - 5.0, 17.5),
    App.Vector(0, 1, 0) # Y軸方向に貫通
)
cut_shapes.append(fuse_hole)

# --- (E) 背面/側面：XIAOマイコン用USB-Cアクセス窓（Y軸方向貫通の四角穴） ---
# スイッチやヒューズの配線と干渉を避けるため、X軸マイナス方向（左後ろ側）の壁を貫通
usb_hole = Part.makeBox(usb_w, wall_t + 10.0, usb_h)
usb_hole.translate(App.Vector(-18.0, -body_r - 5.0, 10.0))
cut_shapes.append(usb_hole)

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

print("003_Body_Base_Case.py: USBポート窓を追加した最新の土台ベースが正常に生成されました！")
