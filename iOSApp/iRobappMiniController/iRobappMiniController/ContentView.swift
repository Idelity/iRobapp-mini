// =========================================================================
// File: iOSApp/iRobappMiniController/iRobappMiniController/ContentView.swift
// Description: iRobapp-mini用 統合コントロール・AI音声会話メイン画面UI（完全修復版）
// =========================================================================

import SwiftUI
import CoreBluetooth
import AVFAudio
// ⚙️ 1. 設定画面専用のパーツ
struct SettingsView: View {
    @Binding var isPremiumAI: Bool
    @Binding var apiKey: String
    @ObservedObject var voiceManager: VoicePipelineManager
    @Environment(\.dismiss) var dismiss
    
    // AIモードの選択肢
    let aiModes = ["ノーマル", "ツンデレ", "ロボット風", "やさしい"]

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("AIエンジンの選択")) {
                    Toggle("有料版 (ChatGPT)", isOn: $isPremiumAI)
                }
                if isPremiumAI {
                    Section(header: Text("OpenAI API認証設定")) {
                        SecureField("sk-...", text: $apiKey)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                        Text("※ユーザー自身のAPIキーを入力してください。").font(.caption).foregroundColor(.gray)
                    }
                } else {
                    Section(header: Text("無料ローカルSLM情報")) {
                        Text("Gemma 2B モデルが有効です。完全オフラインで動作します。").font(.caption).foregroundColor(.gray)
                    }
                }
                // --- オーディオ基本設定 ---
                Section(header: Text("オーディオ設定")) {
                    // ボリューム調整スライダー
                    VStack(alignment: .leading, spacing: 5) {
                        HStack {
                            Text("ボリューム（音圧）")
                            Spacer()
                            Text("\(Int(voiceManager.volumeMultiplier))")
                                .font(.system(.body, design: .monospaced))
                                .foregroundColor(.secondary)
                        }
                        Slider(value: $voiceManager.volumeMultiplier, in: 0...60000, step: 1000)
                    }
                    
                    // モノラル / ステレオ切り替え
                    Toggle(isOn: $voiceManager.isStereoMode) {
                        VStack(alignment: .leading, spacing: 3) {
                            Text("高音量ステレオモード")
                                .font(.body)
                            Text(voiceManager.isStereoMode ? "左右フル駆動（大音量・通信量2倍）" : "モノラル駆動（省通信・標準音量）")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                    }
                }
                // --- BLE通信タイミング調整セクション ---
                Section(header: Text("BLE送信ピッチ調整（細切れ対策）")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Picker("送信ピッチ（Lv）", selection: $voiceManager.bleIntervalLevel) {
                            ForEach(1...8, id: \.self) { level in
                                Text("レベル \(level)").tag(level)
                            }
                        }
                        .pickerStyle(MenuPickerStyle()) // すっきりしたメニュー形式
                        
                        // 現在の具体的なマイクロ秒（μs）をリアルタイムに計算して表示する親切設計
                        HStack {
                            Text("現在のウエイト:")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Spacer()
                            if voiceManager.isStereoMode {
                                Text("\(voiceManager.bleIntervalLevel * 1250) μs (ステレオ)")
                                    .font(.caption.monospaced())
                                    .foregroundColor(.purple)
                            } else {
                                Text("\((voiceManager.bleIntervalLevel * 1250) * 2) μs (モノラル)")
                                    .font(.caption.monospaced())
                                    .foregroundColor(.blue)
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }

                // --- キャラクターボイス設定 ---
                Section(header: Text("キャラクターボイス")) {
                    // ピッチ（声の高さ）調整
                    VStack(alignment: .leading, spacing: 5) {
                        HStack {
                            Text("声のピッチ（高さ）")
                            Spacer()
                            Text(String(format: "%.1f x", voiceManager.pitchRate))
                                .font(.system(.body, design: .monospaced))
                                .foregroundColor(.secondary)
                        }
                        Slider(value: $voiceManager.pitchRate, in: 0.5...2.0, step: 0.1)
                    }
                    
                    // iPhone内部の日本語システム音声選択
                    Picker("声の種類", selection: $voiceManager.selectedVoiceIdentifier) {
                        if voiceManager.availableVoices.isEmpty {
                            Text("標準の日本語音声").tag("")
                        } else {
                            ForEach(voiceManager.availableVoices, id: \.identifier) { voice in
                                Text(voice.name).tag(voice.identifier)
                            }
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                }
                
                // --- AIキャラクター挙動変更 ---
                Section(header: Text("AIキャラクターモード")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Picker("AIモード", selection: $voiceManager.aiMode) {
                            ForEach(aiModes, id: \.self) { mode in
                                Text(mode).tag(mode)
                            }
                        }
                        .pickerStyle(SegmentedPickerStyle())
                        
                        Text(getAiModeDescription(mode: voiceManager.aiMode))
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
            }
            .navigationTitle("システム設定")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("完了") { dismiss() }
                }
            }
        }
    }
    
    // AIモードごとの補足テキスト
    private func getAiModeDescription(mode: String) -> String {
        switch mode {
        case "ツンデレ": return "語尾に「、なんだからね！」が自動で追加されます。"
        case "ロボット風": return "語尾に「。ピッ。ポッ。」が追加され、メカっぽくなります。"
        case "やさしい": return "文頭に「えっとね、」が追加され、おっとりした口調になります。"
        default: return "標準の文章のままおしゃべりします。"
        }
    }
}

// 📱 2. メイン画面の本丸
struct ContentView: View {
    @StateObject private var bleManager = BLEManager()
    @StateObject private var voiceManager = VoicePipelineManager()
    
    @State private var isPremiumAI: Bool = false
    @State private var apiKey: String = ""
    @State private var isShowingSettings: Bool = false
    @State private var debugSpeechText: String = "おはよう"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 15) {
                // 📊 接続ステータス表示エリア
                HStack(spacing: 12) {
                    Circle()
                        .fill(bleManager.isConnected ? Color.green : Color.red)
                        .frame(width: 12, height: 12)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(bleManager.connectedDeviceName).font(.subheadline).fontWeight(.bold)
                        Text(bleManager.isConnected ? "BLE安定接続中" : "ロボットを探索中...").font(.caption).foregroundColor(.gray)
                    }
                    Spacer()
                    if bleManager.isConnected {
                        Button("切断") { bleManager.disconnect() }.font(.caption).foregroundColor(.red)
                    }
                }
                .padding().background(Color(.systemGray6)).cornerRadius(12).padding(.horizontal)
                
                // 📡 ロボット未接続時のスキャンリスト
                if !bleManager.isConnected {
                    VStack(alignment: .leading, spacing: 5) {
                        Text("接続するロボットを選択してください").font(.caption).foregroundColor(.gray).padding(.horizontal)
                        List(bleManager.discoveredPeripherals, id: \.identifier) { peripheral in
                            HStack {
                                Text(peripheral.name ?? "iRobapp-mini").font(.body).fontWeight(.medium)
                                Spacer()
                                Button("接続") { bleManager.connect(to: peripheral) }.buttonStyle(.borderedProminent).controlSize(.small)
                            }
                        }.listStyle(.plain).frame(height: 150)
                    }
                }
                
                // 💬 メイン会話ログ・ディスプレイ
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        if !voiceManager.recognizedText.isEmpty {
                            VStack(alignment: .trailing, spacing: 4) {
                                Text("あなた").font(.caption2).foregroundColor(.gray)
                                Text(voiceManager.recognizedText).padding(10).background(Color.blue.opacity(0.1)).cornerRadius(10)
                            }.frame(maxWidth: .infinity, alignment: .trailing)
                        }
                        
                        if !voiceManager.aiResponseText.isEmpty {
                            VStack(alignment: .leading, spacing: 4) {
                                // 💡【完全修復】Xcodeの頭脳パニックを防ぐため、シンプルなif文に分解！
                                if isPremiumAI {
                                    Text("AI (有料版)").font(.caption2).foregroundColor(.gray)
                                } else {
                                    Text("AI (Gemma 2B 無料版)").font(.caption2).foregroundColor(.gray)
                                }
                                Text(voiceManager.aiResponseText).padding(10).background(Color.green.opacity(0.1)).cornerRadius(10)
                            }.frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }.padding()
                }
                .background(Color(.systemBackground)).border(Color(.systemGray5), width: 1).cornerRadius(12).padding(.horizontal)
                
                // 👁️ 視線手動コントロール（上下左右・十字フル対応版）
                if bleManager.isConnected {
                    VStack(spacing: 8) {
                        // 1段目：上を向くボタン
                        Button("上を向く") {
                            bleManager.sendEyePosition(xValue: 120, yValue: 60)
                        }.buttonStyle(.bordered)
                        
                        // 2段目：左・正面・右を横一列に綺麗に並べる
                        HStack(spacing: 12) {
                            Button("← 左向く") {
                                bleManager.sendEyePosition(xValue: 60, yValue: 120)
                            }.buttonStyle(.bordered)
                            
                            Button(" 正面 ") {
                                bleManager.sendEyePosition(xValue: 120, yValue: 120)
                            }.buttonStyle(.borderedProminent) // 🎯正面は分かりやすく目立たせる
                            
                            Button("右向く →") {
                                bleManager.sendEyePosition(xValue: 180, yValue: 120)
                            }.buttonStyle(.bordered)
                        }
                        
                        // 3段目：下を向くボタン
                        Button("下を向く") {
                            bleManager.sendEyePosition(xValue: 120, yValue: 180)
                        }.buttonStyle(.bordered)
                    }
                    .padding(.vertical, 8)
                }
                if bleManager.isConnected {
                    VStack(alignment: .leading, spacing: 5) {
                        
                        HStack(spacing: 8) {
                            // ✍️ 好きな文章を打ち込める入力欄
                            TextField("テストする文章を入力", text: $debugSpeechText)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .submitLabel(.done)
                            
                            // ▶️ 入力欄の文字列を直撃でTTSストリーミングするボタン
                            Button(action: {
                                // 通常のAI処理（工程1〜4）を完全にスキップして、このテキストを直接再生！
                                voiceManager.speakAndStream(text: debugSpeechText)
                            }) {
                                HStack(spacing: 4) {
                                    Image(systemName: "play.fill")
                                    Text("再生")
                                }
                                .font(.subheadline)
                                .bold()
                                .foregroundColor(.white)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 8)
                                .background(debugSpeechText.isEmpty ? Color.gray : Color.blue)
                                .cornerRadius(8)
                        }
                        // 再生中や録音中、または文字が空の時はボタンを押せなくする
                        .disabled(voiceManager.isSpeaking || voiceManager.isRecording || debugSpeechText.isEmpty)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                    .padding(.horizontal, 15) // 画面全体の左右マージンに合わせる
                }
                
                Spacer()
                
                // 🎙️ 音声対話・プッシュトークボタン
                if bleManager.isConnected {
                    VStack(spacing: 8) {
                        Button(action: {
                            if voiceManager.isRecording { voiceManager.stopRecording() }
                            else { voiceManager.startRecording() }
                        }) {
                            Image(systemName: voiceManager.isRecording ? "stop.fill" : "mic.fill")
                                .font(.title).foregroundColor(.white).padding(25)
                                .background(voiceManager.isRecording ? Color.red : Color.blue).clipShape(Circle()).shadow(radius: 4)
                        }
                        Text(voiceManager.isRecording ? "話終わったらもう一度押してね" : "ボタンを押しておしゃべり").font(.footnote).foregroundColor(.gray)
                    }.padding(.bottom, 10)
                }
            }
            .navigationTitle("iRobapp")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { isShowingSettings = true }) { Image(systemName: "gearshape.fill") }
                }
            }
            .sheet(isPresented: $isShowingSettings) {
                SettingsView(isPremiumAI: $isPremiumAI, apiKey: $apiKey,voiceManager: voiceManager)
            }
            .onAppear {
                voiceManager.setup(bleManager: bleManager)
                bleManager.startScanning()
                
                // 🌟 音声認識が完了した時の対話パイプラインの挙動
                voiceManager.onSpeechRecognized = { text in
                    if !isPremiumAI {
                        // 🌟 重いAI推論はグローバル（バックグラウンド）キューで実行
                        DispatchQueue.global(qos: .userInitiated).async {
                            // ※もし GemmaAIManager.shared があればそちらを推奨します
                            let gemma = GemmaAIManager()
                            gemma.generateLocalResponse(prompt: text) { reply in
                                // 🌟 UIの更新とBLE送信トリガーは必ずメインスレッドに戻す
                                DispatchQueue.main.async {
                                    voiceManager.speakAndStream(text: reply)
                                }
                            }
                        }
                    } else {
                        // 有料版（クラウド）の模擬処理
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                            let cloudReply = "「\(text)」ですね。クラウドでお返事しています。"
                            voiceManager.speakAndStream(text: cloudReply)
                        }
                    }
                }
            }
        }
    }
}

