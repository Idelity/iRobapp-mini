# =========================================================
# File: 006_20mm_Adjuster.py
# Description: iRobapp-mini用 胴体アジャスター（20mm版）
# Spec: ボディケース（50x60、内寸44x54）に完全適合する長方形アジャスタ
# =========================================================
import FreeCAD as App
import Part

doc_name = "iRobapp_mini_Correct_Corner_Pin_Adjuster"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# ボディ＆底蓋のパラメータ（mm単位）
# ---------------------------------------------------------
body_w = 50.0          # X軸方向の外幅
body_l = 60.0          # Y軸方向の外長さ
wall_t = 3.0           # 外壁の肉厚 3mm
adjuster_h = 20.0      # アジャスターの純粋な高さ（20mm）

lid_rib_size = 4.0     # 蓋受けリブのサイズ (4mm)
screw_r_m2   = 1.1     # M2ネジ用穴（半径1.1mm）

# ネジ穴の中心座標
screw_offset_x = 20.0
screw_offset_y = 25.0

# 内壁の限界座標
inner_w_half = body_w / 2.0 - wall_t  # 22.0mm
inner_l_half = body_l / 2.0 - wall_t  # 27.0mm

# はめ合い用のクリアランス（3D印刷の太り対策）
clearance = 0.2

# ---------------------------------------------------------
# 1. アジャスターの基本枠（外寸50x60, 内寸44x54, 高さ20mm）
# ---------------------------------------------------------
outer_box = Part.makeBox(body_w, body_l, adjuster_h)
outer_box.translate(App.Vector(-body_w / 2.0, -body_l / 2.0, 0.0))

inner_box = Part.makeBox(body_w - (wall_t * 2.0), body_l - (wall_t * 2.0), adjuster_h + 2.0)
inner_box.translate(App.Vector(-(body_w - wall_t * 2.0) / 2.0, -(body_l - wall_t * 2.0) / 2.0, -1.0))

adjuster_combined = outer_box.cut(inner_box)

# ---------------------------------------------------------
# 2. 4つ角の肉盛柱（Pillar）の追加（上下を貫通するネジ穴の土台）
# ---------------------------------------------------------
for sx in [-1, 1]:
    for sy in [-1, 1]:
        corner_pillar = Part.makeBox(lid_rib_size, lid_rib_size, adjuster_h)
        rx = (inner_w_half - lid_rib_size) if sx > 0 else -inner_w_half
        ry = (inner_l_half - lid_rib_size) if sy > 0 else -inner_l_half
        corner_pillar.translate(App.Vector(rx, ry, 0.0))
        adjuster_combined = adjuster_combined.fuse(corner_pillar)

# ---------------------------------------------------------
# 3. 上部：底蓋を受け止める「一段低い段差（3mm凹）」の作成
# ---------------------------------------------------------
upper_pocket = Part.makeBox(body_w - (wall_t * 2.0), body_l - (wall_t * 2.0), 3.1)
upper_pocket.translate(App.Vector(-(body_w - wall_t * 2.0) / 2.0, -(body_l - wall_t * 2.0) / 2.0, adjuster_h - 3.0))
adjuster_combined = adjuster_combined.cut(upper_pocket)

# ---------------------------------------------------------
# 4. 下部【修正】：ボディのリブ上の凹みにカチッとハマる「4つ角の凸ボス（足）」
# ---------------------------------------------------------
# 外周の縁はフラット（Z=0）のまま、4つ角のネジ穴部分だけを下に3mm突出させます
joint_h = 3.0  # ボディ天面からリブ上面までの深さ3mm

for sx in [-1, 1]:
    for sy in [-1, 1]:
        # クリアランスを考慮した突起サイズ（4mmより少し小さくする）
        pin_size = lid_rib_size - clearance
        bottom_pin = Part.makeBox(pin_size, pin_size, joint_h)
        
        # ボディ側のリブ位置（4つ角）にぴったり合うように配置をオフセット
        rx = (inner_w_half - lid_rib_size + clearance / 2.0) if sx > 0 else (-inner_w_half + clearance / 2.0)
        ry = (inner_l_half - lid_rib_size + clearance / 2.0) if sy > 0 else (-inner_l_half + clearance / 2.0)
        
        # Z=0 から下方向（-3mm）に突起を伸ばす
        bottom_pin.translate(App.Vector(rx, ry, -joint_h))
        
        # アジャスター本体と結合
        adjuster_combined = adjuster_combined.fuse(bottom_pin)

# ---------------------------------------------------------
# 5. くり抜き処理：4つ角のM2ネジ貫通穴（下向きの突起の底まで完全に貫通）
# ---------------------------------------------------------
for sx in [-1, 1]:
    for sy in [-1, 1]:
        screw_hole = Part.makeCylinder(
            screw_r_m2,
            adjuster_h + joint_h + 4.0,
            App.Vector(screw_offset_x * sx, screw_offset_y * sy, -joint_h - 2.0),
            App.Vector(0, 0, 1)
        )
        adjuster_combined = adjuster_combined.cut(screw_hole)

# ---------------------------------------------------------
# 6. ドキュメントへの出力
# ---------------------------------------------------------
adjuster_part = doc.addObject("Part::Feature", "iRobapp_mini_20mm_Adjuster")
adjuster_part.Shape = adjuster_combined

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("006_006_20mm_Adjuster.py: 出力しました。")

