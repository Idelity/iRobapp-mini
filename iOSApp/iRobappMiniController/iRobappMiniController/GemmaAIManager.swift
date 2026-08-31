// =========================================================================
// File: iOSApp/iRobappMiniController/iRobappMiniController/GemmaAIManager.swift
// Description: iRobapp-mini用 Gemma 2B 完全ローカルオンデバイスAI推論管理クラス（BOSループ完全対策版）
// =========================================================================

import Foundation
import Combine
import MediaPipeTasksGenAI

class GemmaAIManager: ObservableObject {
    @Published var isModelLoading: Bool = false
    @Published var isThinking: Bool = false
    
    private var llmInference: MediaPipeTasksGenAI.LlmInference?
    
    private var localModelPath: String? {
        return Bundle.main.path(forResource: "gemma-2b-it-gpu-int4", ofType: "bin")
    }
    
    init() {
        if let path = localModelPath {
            print(">>> 🧠 本物のローカルAI（Gemma 2B）のファイルを検知しました。")
            setupModel(modelPath: path)
        } else {
            print("⚠️ 警告: gemma-2b-it-gpu-int4.bin が見つかりません。")
        }
    }
    
    private func setupModel(modelPath: String) {
        DispatchQueue.main.async {
            self.isModelLoading = true
        }
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            
            let options = MediaPipeTasksGenAI.LlmInference.Options(modelPath: modelPath)
            do {
                self.llmInference = try MediaPipeTasksGenAI.LlmInference(options: options)
                print("🟩 Gemma 2B モデルの初期化に成功しました！")
                DispatchQueue.main.async {
                    self.isModelLoading = false
                }
            } catch {
                print("❌ 初期化失敗: \(error)")
                DispatchQueue.main.async {
                    self.isModelLoading = false
                }
            }
        }
    }
    
    // 🟩 修正：AIが最もパニックを起こしにくい、超シンプルなチャット構造に変換
    private func wrapPrompt(_ rawPrompt: String) -> String {
        return "ユーザー: \(rawPrompt)\nシステム: "
    }
    
    // 🟩 修正：届いたテキストからシステム記号を跡形もなく消し去る強力クリーナー
    private func cleanText(_ rawText: String) -> String {
        return rawText
            .replacingOccurrences(of: "<bos>", with: "")
            .replacingOccurrences(of: "<eos>", with: "")
            .replacingOccurrences(of: "<start_of_turn>", with: "")
            .replacingOccurrences(of: "<end_of_turn>", with: "")
            .replacingOccurrences(of: "model", with: "")
            .replacingOccurrences(of: "user", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    // 🧠 ① 一括で答えを受け取る関数（View側が135行目付近の.onAppear内で呼んでいるメイン関数）
    func generateLocalResponse(prompt: String, completion: @escaping (String) -> Void) {
        guard let inference = llmInference else {
            completion("エラー：モデルが準備できていません。")
            return
        }
        
        DispatchQueue.main.async { self.isThinking = true }
        
        let formattedPrompt = "システム: あなたは日本語で答えてください。出力は必ず日本語の自然文のみでお願いします。\nユーザー: \(prompt)\nシステム: "
        
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            do {
                let realReply = try inference.generateResponse(inputText: formattedPrompt)
                let finalReply = self.cleanText(realReply)
                
                // 万が一クリーニングしても中身が空っぽかシステムタグだけだった場合のセーフティ
                let safeReply = finalReply.isEmpty ? "（首をかしげている）" : finalReply
                
                DispatchQueue.main.async {
                    self.isThinking = false
                    completion(safeReply)
                }
            } catch {
                DispatchQueue.main.async {
                    self.isThinking = false
                    completion("エラーが発生しました。")
                }
            }
        }
    }

    // 🧠 ② ストリーミング関数（View側の型エラーを完全に沈黙させるためのダミー互換配置）
    func generateLocalResponseStream(prompt: String, completion: @escaping (String) -> Void) {
        generateLocalResponse(prompt: prompt, completion: completion)
    }
    
    // 🧠 ③ ストリーミング関数（引数3つバージョンも同名で用意し、135行目のエラーを完全消滅させます）
    func generateLocalResponseStream(prompt: String, onChunk: @escaping (String) -> Void, completion: @escaping (String) -> Void) {
        generateLocalResponse(prompt: prompt, completion: completion)
    }
}

