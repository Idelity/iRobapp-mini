# =========================================================
# File: 003_ESP32S3_Mount.py
# Description: iRobapp-mini用 ESP32-S3固定パーツ（3部品合体・積層状態）
# Spec: 頭部幅11.5mm / 中間・押さえ幅6.0mm / 中間パーツ厚み22.0mmへ変更
# =========================================================

import FreeCAD as App
import Part

doc_name = "iRobapp_mini_ESP32S3_Mount"

if App.getDocument(doc_name):
    App.closeDocument(doc_name)

doc = App.newDocument(doc_name)

# ---------------------------------------------------------
# パラメータ設定
# ---------------------------------------------------------
head_w = 11.5   # 頭部パーツの幅（10mmのUSB穴を通すため維持）
body_w = 6.0    # 中間パーツと押さえパーツの幅: 6.0mm

# ---------------------------------------------------------
# 1. 頭部パーツ (パーツA) -> 【前面の壁・1.5mm上方移動】
# 仕様: 高さ7mm, 幅11.5mm, 厚さ3mm / USB穴 10mm x 4mm（上下中央配置）
# ---------------------------------------------------------
p1_h = 7.0
p1_t = 3.0

part1_base = Part.makeBox(head_w, p1_t, p1_h)
part1_base.translate(App.Vector(-head_w / 2.0, -p1_t, 0.0))

# USB用の穴（10mm x 4mm）を頭部パーツの上下中央に作成してくり抜く
usb_w = 10.0
usb_h = 4.0
usb_void = Part.makeBox(usb_w, p1_t + 2.0, usb_h)
usb_void.translate(App.Vector(-usb_w / 2.0, -p1_t - 1.0, (p1_h - usb_h) / 2.0))
part1_shape = part1_base.cut(usb_void)

# 頭部パーツと穴を合わせて1.5mm上に移動
part1_shape.translate(App.Vector(0.0, 0.0, 1.5))

# ---------------------------------------------------------
# 2. 中間パーツ (パーツB) -> 【中央の底面ベッド】
# 仕様: 高さ3mm, 幅6.0mm, 厚さ22.0mm（変更）
# ---------------------------------------------------------
p2_h = 3.0
p2_t = 22.0  # 【変更】厚みを20mmから22mmに変更

part2_shape = Part.makeBox(body_w, p2_t, p2_h)
part2_shape.translate(App.Vector(-body_w / 2.0, 0.0, 0.0))

# ---------------------------------------------------------
# 3. 押さえパーツ (パーツC) -> 【後ろ面の壁】
# 仕様: 高さ8mm, 幅6.0mm, 厚さ3mm
# ---------------------------------------------------------
p3_h = 8.0
p3_t = 3.0

part3_shape = Part.makeBox(body_w, p3_t, p3_h)
# 中間パーツの後ろ面（Y = 新しいp2_tである22.0mm）にぴったり接するように配置
part3_shape.translate(App.Vector(-body_w / 2.0, p2_t, 0.0))

# ---------------------------------------------------------
# 4. 形状の合体 (ブーリアン結合)
# ---------------------------------------------------------
# 3つのソリッドを一体化
combined_shape = part1_shape.fuse(part2_shape).fuse(part3_shape)

# ドキュメントへの追加
esp_mount = doc.addObject("Part::Feature", "ESP32S3_Mount")
esp_mount.Shape = combined_shape

# ---------------------------------------------------------
# ドキュメントの再計算と画面フィット
# ---------------------------------------------------------
doc.recompute()

if hasattr(App, "Gui") and App.Gui.ActiveDocument and App.Gui.ActiveDocument.ActiveView:
    App.Gui.ActiveDocument.ActiveView.fitAll()

print("005_ESP32S3_Mount.py: 出力しました。")

