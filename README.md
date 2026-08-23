# iRobapp-mini
AI＋ロボット＋アプリケーションの三位一体で生まれる卓上マスコット「iRobapp」の軽量版プロトタイプ

## 📂 ディレクトリ構成 (Directory Structure)

```text
iRobapp-mini/
├── 📁 cad/                       # ハードウェア設計データ
│   ├── 📁 scripts/               # FreeCAD用のPython生成スクリプト
│   └── 📁 stl/                   # 3Dプリンター出力用のSTLファイル
├── 📁 docs/                      # プロジェクトの解説ドキュメント
│   ├── concept.md                # iRobapp-miniのコンセプトガイド
│   └── assembly.md               # ハードウェアの組み立て手順書
├── 📁 firmware/                  # XIAO ESP32-S3用のコード
│   ├── 📁 main/                  # メインの制御ファームウェア
│   └── 📁 eye_assets/            # GC9A01液晶に表示する目の画像・アニメーションデータ
├── 📁 iOSApp/                    # Xcode
│   └── 📁 iRobappMiniController/ # iPhoneアプリのコード
├── .agents                       # GitHub Copilot用のエージェント指示書
├── .gitignore                    # 不要なファイル（FreeCADのバックアップ等）を除外する設定
└── README.md                     # プロジェクトの全体説明書
```
