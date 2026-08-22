# =========================================================
# File: 004_Bottom_Lid_Battery_Holder.py
# Description: iRobapp-mini用 バッテリーホルダー付き底蓋
# Spec: 003番の底面(内径64mm)に適合 / LiPoバッテリー固定リブ仕様
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
lid_clearance = 0.4    # 3Dプリント時の嵌め合い用クリアランス（片側0.2mm）

# 003_Body_Base_Caseの寸法から底蓋のサイズを自動計算
body_r = 35.0          # 003の底面外径半径
lid_r  = body_r - wall_t - lid_clearance  # 底蓋の半径（約31.6mm、直径約63.2mm）

# 想定するLiPoバッテリーの最大寸法（クリアランス込み）
# 例：500mAh〜800mAhクラス（厚み7.5mm × 幅25.5mm × 長さ40.0mmなどに対応）
batt_w = 26.0          # バッテリーの幅
batt_h = 8.0           # バッテリーの厚み（ホールド壁の高さ）

# ---------------------------------------------------------
# 1. 底蓋ベース形状の作成（薄い円盤構造）
# ---------------------------------------------------------
# 厚み2mmの円盤をベースにします
lid_base = Part.makeCylinder(lid_r, 2.0)

# ---------------------------------------------------------
# 2. バッテリーをホールドする固定リブ（壁）の作成
# ---------------------------------------------------------
# バッテリーを左右から挟み込むための2本の固定壁（リブ）を作ります
rib_thick = 2.0        # リブ自体の厚み
rib_length = 30.0      # リブの長さ（バッテリーをしっかり保持する長さ）

# 1本目のホールド壁
rib1 = Part.makeBox(rib_length, rib_thick, batt_h)
# 円盤の中央（X軸中心）に配置し、Y軸方向にバッテリー幅の半分だけオフセット
rib1.translate(App.Vector(-rib_length / 2.0, (batt_w / 2.0), 2.0))

# 2本目のホールド壁
rib2 = Part.makeBox(rib_length, rib_thick, batt_h)
rib2.translate(App.Vector(-rib_length / 2.0, -(batt_w / 2.0) - rib_thick, 2.0))

# 円盤と2本のリブを一体化
main_body = lid_base.fuse(rib1).fuse(rib2)

# ---------------------------------------------------------
# 3. くり抜き・ディテール処理 ＆ ドキュメント出力
# ---------------------------------------------------------
# 今回はくり抜き処理（cut）は行わず、fuseのみのクリーンなソリッドを出力します
final_shape = main_body

lid_part = doc.addObject("Part::Feature", "Bottom_Lid_Battery_Holder")
lid_part.Shape = final_shape

doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("004_Bottom_Lid_Battery_Holder.py: バッテリーホルダー付き底蓋が正常に生成されました！")
