# iRobapp-mini
AI＋ロボット＋アプリケーションの三位一体で生まれる卓上マスコット「iRobapp」の軽量版プロトタイプ

## 📂 ディレクトリ構成 (Directory Structure)

```text
iRobapp-mini/
├── 📁 cad/                       # ハードウェア設計データ
│   ├── 📁 scripts/               # FreeCAD用のPython生成スクリプト
│   └── 📁 stl/                   # 3Dプリンター出力用のSTLファイル
├── 📁 docs/                      # プロジェクトの解説ドキュメント
│   ├── assembly-guide.md         # iRobapp-miniハードウェアの組み立て手順書
│   ├── component-dimensions.md   # iRobapp-miniパーツ寸法表（FreeCAD設計基準）
│   ├── concept.md                # iRobapp-miniのコンセプトガイドについては下記を参照
│   ├── contributing.md           # 開発者向け：ローカル環境構築 ＆ 開発開始手順書
│   ├── development-log.md        # iRobapp-mini 開発日記 
│   ├── pinout-wiring-table.md    # iRobapp-mini ピンアサイン・配線表
│   └── system-specifications.md  # iRobapp-mini ソフトウェア・システム機能仕様書
├── 📁 firmware/                  # XIAO ESP32-S3用のコード
│   ├── 📁 main/                  # メインの制御ファームウェア
│   └── 📁 eye_assets/            # GC9A01液晶に表示する目の画像・アニメーションデータ
├── 📁 iOSApp/                    # Xcode
│   └── 📁 iRobappMiniController/ # iPhoneアプリのコード
├── .agents                       # GitHub Copilot用のエージェント指示書
├── .gitignore                    # 不要なファイル（FreeCADのバックアップ等）を除外する設定
└── README.md                     # プロジェクトの全体説明書
```
## 📄 iRobapp Documentation

- 🇯🇵 Japanese Concept Guide（日本語版コンセプトガイド）  
  https://github.com/Idelity/iRobapp/blob/main/docs/iRobapp-concept.md

- 🌍 English Concept Guide  
  https://github.com/Idelity/iRobapp/blob/main/docs/iRobapp-concept-en.md



> [!💡 お知らせ / Notice]
> 本家プロジェクト **[iRobapp](https://github.com/Idelity/iRobapp)** は、こちらを参照してください。
> 並行稼働プロジェクト **[Mocapy（モカピー）](https://github.com/Idelity/Mocapy)** は、こちらを参照してください。
> 
