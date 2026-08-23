// =========================================================================
// File: iOSApp/iRobappMiniController/iRobappMiniController/ContentView.swift
// Description: iRobapp-mini用 統合コントロール・AI音声会話メイン画面UI（完全修復版）
// =========================================================================

import SwiftUI
import CoreBluetooth

// ⚙️ 1. 設定画面専用のパーツ
struct SettingsView: View {
    @Binding var isPremiumAI: Bool
    @Binding var apiKey: String
    @Environment(\.dismiss) var dismiss
    
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
            }
            .navigationTitle("システム設定")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("完了") { dismiss() }
                }
            }
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
                
                // 👁️ 視線手動コントロール
                if bleManager.isConnected {
                    HStack(spacing: 12) {
                        Button("上を向く") { bleManager.sendEyePosition(yValue: 60) }.buttonStyle(.bordered)
                        Button("正面") { bleManager.sendEyePosition(yValue: 120) }.buttonStyle(.bordered)
                        Button("下を向く") { bleManager.sendEyePosition(yValue: 180) }.buttonStyle(.bordered)
                    }
                    .padding(.vertical, 5)
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
                SettingsView(isPremiumAI: $isPremiumAI, apiKey: $apiKey)
            }
            .onAppear {
                voiceManager.setup(bleManager: bleManager)
                bleManager.startScanning()
                voiceManager.onSpeechRecognized = { text in
                    if !isPremiumAI {
                        let gemma = GemmaAIManager()
                        gemma.generateLocalResponse(prompt: text) { reply in
                            voiceManager.speakAndStream(text: reply)
                        }
                    } else {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                            let cloudReply = "（有料版モック）「\(text)」ですね。クラウドでお返事しています。"
                            voiceManager.speakAndStream(text: cloudReply)
                        }
                    }
                }
            }
        }
    }
}

