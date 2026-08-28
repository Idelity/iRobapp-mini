# 💻 開発者向け：ローカル環境構築 ＆ 開発開始手順書

本ドキュメントは、新しくプロジェクトに参加する開発者が、GitHubから『iRobapp-mini』のソースコードをダウンロード（クローン）し、Macローカル環境で即座に開発・実機テストを開始するための公式スタートガイドです。

すでに完成されたフォルダ構造（`iOSApp/` や `firmware/`）がリポジトリ内に構築されているため、新規でプロジェクトを作成したり、フォルダを引っ越しさせたりする手順は一切不要です。

---

## 📥 ステップ1：ソースコードのダウンロード（Git Clone）

Macの「ターミナル」アプリを開き、コードを展開したいフォルダ（例：書類フォルダ）へ移動して、リポジトリを丸ごとダウンロードします。

```bash
# 1. Macの「書類 (Documents)」フォルダへ移動
cd ~/Documents/

# 2. GitHubからiRobapp-miniのリポジトリを丸ごとローカルに複製（クローン）
git clone https://github.com/Idelity/iRobapp-mini

# 3. クローン完了後、自動作成された「iRobapp-mini」フォルダが作成されますので中身を確認してください。
cd iRobapp-mini
```

---

## 📱 ステップ2：iPhoneアプリ（iOSApp）の開発開始手順

リポジトリ内の `iOSApp` フォルダの中には、すでに最適化されたXcodeプロジェクトが格納されています。

1. Macの「Finder」で `~/Documents/iRobapp-mini/iOSApp/iRobappMiniController/` フォルダを開きます。
2. フォルダ内にある **`iRobappMiniController.xcodeproj`** （白いXcodeのアイコンファイル）をダブルクリックして開きます。
3. **【超重要：実機ビルドのためのSigning設定】**
   * Xcodeが起動したら、左側のナビゲーター一番上にある青いアイコン（`iRobappMiniController`）をクリックします。
   * 中央エディタの上部タブから **［Signing & Capabilities］** を開きます。
   * ［Automatically manage signing］にチェックが入っていることを確認します。
   * **［Team］** のプルダウンメニューから、ご自身のApple ID（Personal Teamなど）を選択します。
4. MacにiPhoneをケーブルで接続し、Xcode画面左上のデバイス選択でご自身のiPhoneを選んで、**［▶（Run）］ボタン** を押せば、アプリが実機に転送されスキャンがスタートします。

---

## 🧠 ステップ3：【無料版AI用】Gemma 2B モデルファイルのダウンロード ＆ 配置手順

本プロジェクトの無料版（ローカルオンデバイスAI）を動作させるためには、Googleが公式提供する大容量のAIモデルファイル（約1.35GB）を【手動で】Mac内に配備する必要があります。
※このファイルは超大容量のため、`.gitignore` のセキュリティフィルターにより、GitHubへのプッシュ対象からは自動で完全除外されます。


### 📥 [手順3-1] モデルファイルのダウンロード
1. Webブラウザで [KaggleのGoogle公式Gemmaモデル配布ページ](https://kaggle.com) にアクセスします。
2. **【重要：アカウント登録と規約同意】**
   * モデルファイルをダウンロードするには、**Kaggleの無料アカウント登録（Googleアカウント等で1分で作成可能）とログインが必須**です。
   * ログイン後、画面上に表示されるGoogleのGemma利用規約（ライセンス）を確認し、**［Accept（同意する）］** または **［Request Access］** ボタンを押してダウンロード権限を有効化してください。
3. WebブラウザでKaggleにログインし、左側メニューの **［Models］** をクリックします。
4. 画面上部の検索窓に **`Gemma`** と入力し、検索結果の一番上にあるGoogle公式の **「Gemma」** の親ページを開きます。
5. Model Variationsに表示されている項目よりLiteRTをクリックします。
6. VARIATIONでgemma-2b-it-gpu-int4を選択してダウンロードします。
> **【初回のみ：Google公式ライセンス同意画面が出ます】**
>   * 選択後、ファーストネーム、ラストネーム、メールアドレスの入力を求められる画面が立ち上がります。
>   * これはGoogle公式のGemma利用規約フォームです。名前とアドレスをローマ字で入力し、規約同意のチェックを入れて ［Submit（送信）］ を押してください。
6. **【圧縮パックのダウンロードと解凍方法】**
   * ダウンロード完了後、Macの「ダウンロード」フォルダにある `gemma-tflite-gemma-2b-it-gpu-int4-v1.tar` ファイルをダブルクリックして解凍してください。
7. **【ファイルの配置とリネーム手順（超重要）】**
   * 解凍されたフォルダ内にある **`gemma-2b-it-gpu-int4.bin`**という1.35GBのファイルを見つけてください。
   * このファイルが、本プロジェクトのXcodeで読み込む本物のAIモデルファイルとなります。


> 💡 **Kaggle（カグル）とは？**
> Google傘下の世界最大のAI・データサイエンスプラットフォームです。本プロジェクトでは、Googleが公式に検証・配布している安全な「Gemma 2B」の正規バイナリファイルを取得するためにKaggleを利用します。

---

### 📂 [手順3-2] Macローカルフォルダへの正しい保存
ダウンロードしたファイルを、MacのFinderを使い、以下の「本丸（ソースコードが詰まった内側のフォルダ）」の中に移動（コピー）します。

```text
/Users/irobapp-dev01/Documents/iRobapp-mini/
└── 📁 iOSApp/
    └── 📁 iRobappMiniController/ (外箱フォルダ)
        ├── 📄 iRobappMiniController.xcodeproj
        └── 📁 iRobappMiniController/ (内側：コードフォルダ)
            ├── 📄 BLEManager.swift
            ├── 📄 VoicePipelineManager.swift
            ├── 📄 ContentView.swift
            └── 📄 gemma-2b-it-gpu-int4.bin  <-- ★ここへ直接保存する！
```

---

### ⚙️ [手順3-3] Xcodeへの LiteRTLM 導入手順 (SPM)
すでにインストール済みの場合は手順3−4を実施してください。

1. Xcodeでプロジェクトを開き、メニューの File ＞ Add Package Dependencies... を選択します。

2. 検索窓に公式リポジトリのURL https://github.com/google-ai-edge/LiteRT-LM を入力します。

3. LiteRTLM ライブラリを選択し、アプリのターゲットに追加してインストールを完了します。


---

### ⚙️ [手順3-4] CocoaPodsのインストール

1. Macの「ターミナル」アプリを開き、以下のコマンドを貼り付けてEnterを押してください。

```bash
brew install cocoapods
```

2. インストールが成功したか確認する。以下のコマンドを貼り付けてEnterを押してください。

```bash
pod --version
```
>画面に 1.15.2（またはそれに近い数字）とバージョンが表示されれば、導入完了です！


---

## 💾 ステップ4：ソースコードのアップロード（Git push）

xcodeの修正や設定変更を終えたら「ターミナル」アプリを開き、次のコマンドを実施する。

```bash
# 1. リポジトリフォルダへ移動
cd ~/Documents/iRobapp-mini
# 2. 未反映のファイルをローカルに反映する。
git pull --rebase origin main
# 3. 新規ファイルや変更内容を反映する。
git add .
# 4. ローカルにセーブポイントを刻む。
git commit -m "ここに適切なコメントを記入する"
# 5. リポジトリに反映する。
git push origin main
```

---



## 💾 ステップ5：ロボット側（firmware）の書き込み手順

1. Arduino IDEを起動し、`~/Documents/iRobapp-mini/firmware/main/main.ino` を開きます。
2. ライブラリマネージャー（📚マーク）から **`ESP32Servo`** および **`LovyanGFX`** をインストールします。
3. パソコンにXIAO ESP32-S3を接続し、ボードとポートを正しく選択して **［➔（書き込み）］ボタン** を押します。


## 🏷️ コミットメッセージの記載ルール（重要マナー）

本プロジェクトでは、コミットの歴史を綺麗に保つため、世界標準の「Conventional Commits」ルールを採用しています。コミット時は、メッセージの先頭に必ず以下のラベル（プレフィックス）を付与してください。

*   `feat:` — 新しい機能、画面、通信ロジックなどの追加
*   `fix:` — バグ修正やコンパイルエラーの解消
*   `docs:` — 説明書（Markdownファイル）やREADMEの更新のみ
*   `refactor:` — 動作を変えない、コードの綺麗な整理整頓

💡 **詳しい仕様や他のラベルについては、以下の日本語チートシートを参考にしてください：**
*   [Conventional Commits 公式仕様書（日本語）](https://conventionalcommits.org)
*   [Conventional Commits クイックチートシート（Qiita）](https://qiita.com)


