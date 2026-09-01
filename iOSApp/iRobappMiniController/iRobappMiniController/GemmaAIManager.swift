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
    private var robotName: String {
        return UserDefaults.standard.string(forKey: "saved_robot_name") ?? "モカピー"
    }

    private var firstPerson: String {
        return UserDefaults.standard.string(forKey: "saved_first_person") ?? "ぼく"
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
            // 以下のパラメータで同じ文のループ確率を大幅に下げます
            options.maxTokens = 128        // 無駄な長文や無限ループを出力させない安全弁

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

    private func getCurrentDateTimeString() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ja_JP") // 日本語表記を強制
        formatter.timeZone = TimeZone.current          // 端末の現在時刻
        formatter.dateFormat = "yyyy年M月d日E曜日 H:mm"  // 2026年9月1日火曜日 11:36 の形
        
        return formatter.string(from: Date())
    }
    
    // 🟩 修正：AIが最もパニックを起こしにくい、超シンプルなチャット構造に変換
    private func wrapPrompt(_ rawPrompt: String) -> String {
        let currentDateTime = getCurrentDateTimeString()
//        return "ユーザー: \(rawPrompt)\nシステム: "
//        return "システム: あなたは日本語で答えてください。出力は必ず日本語の自然文のみでお願いします。\nユーザー: \(rawPrompt)\nアシスタント: "
        return """
        <start_of_turn>user
        前提条件：あたなの名前は\(robotName)です。一人称は\(firstPerson)です。日時：\(currentDateTime)
        指示：あなたは親切な日本のロボットアシスタントです。中国語や英語を混ぜず、自然な日本語のみで短く回答してください。
        質問: \(rawPrompt)<end_of_turn>
        <start_of_turn>model
        
        """
    }
    
    // 🟩 修正：届いたテキストからシステム記号を跡形もなく消し去る強力クリーナー
/*
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
*/
    private func cleanText(_ rawText: String) -> String {
        var cleaned = rawText
            .replacingOccurrences(of: "<bos>", with: "")
            .replacingOccurrences(of: "<eos>", with: "")
            .replacingOccurrences(of: "<start_of_turn>", with: "")
            .replacingOccurrences(of: "<end_of_turn>", with: "")
            .replacingOccurrences(of: "model\n", with: "")
            .replacingOccurrences(of: "user\n", with: "")
        
        // 稀に「アシスタント: おはよう！」のようにプレフィックスが残る場合の対策
        if cleaned.hasPrefix("model") { cleaned.removeFirst(5) }
        if cleaned.hasPrefix("assistant") { cleaned.removeFirst(9) }
        
        return cleaned.trimmingCharacters(in: .whitespacesAndNewlines)
    }
    // 🧠 ① 一括で答えを受け取る関数（View側が135行目付近の.onAppear内で呼んでいるメイン関数）
    func generateLocalResponse(prompt: String, completion: @escaping (String) -> Void) {
        guard let inference = llmInference else {
            completion("エラー：モデルが準備できていません。")
            return
        }
        
        DispatchQueue.main.async { self.isThinking = true }
        
        //let formattedPrompt = "ユーザー: \(prompt)\nアシスタント: "
        //let formattedPrompt = "user\n日本語で答えてください。\n\(prompt)\nmodel\n"
        //let formattedPrompt = "user\nRespond in Japanese only.\n\(prompt)\nmodel\n"
        //let formattedPrompt = "user\nあなたは日本語のアシスタントです。以下の質問に日本語で答えてください。\n\(prompt)\nmodel\n"
        // 長ったらしい英文が出力されるだけだったパターン
        //let formattedPrompt = "user\n\(prompt)\nmodel\n"
        //いい感じだけど、英文で返却される。
        //let formattedPrompt = "<start_of_turn>user\n\(prompt)<end_of_turn>\n<start_of_turn>model\n"
        //let formattedPrompt = "<start_of_turn>user\n\(prompt)に対して日本語で答えてください。中国語は混ぜないでください。<end_of_turn>\n<start_of_turn>model\n"
        let formattedPrompt = wrapPrompt(prompt)
        
        print("DEBUG: formattedPrompt=\(formattedPrompt)")

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

