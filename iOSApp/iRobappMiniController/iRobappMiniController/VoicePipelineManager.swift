// =========================================================================
// File: iOSApp/VoicePipelineManager.swift
// Description: iRobapp-mini用 音声認識(STT) ＆ リアルタイム音声ストリーミング(TTS) [設定機能連動版]
// =========================================================================

import Foundation
import Speech
import AVFoundation
import Combine

class VoicePipelineManager: NSObject, ObservableObject, SFSpeechRecognizerDelegate, AVSpeechSynthesizerDelegate {
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "ja-JP"))
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()
    
    private let synthesizer = AVSpeechSynthesizer()
    private var bleManager: BLEManager?
    // BLEの1パケットあたりの送信サイズ制限（Write Without Responseの安全値）
    private let packetSize = 180
    // 発話ごとに一時的に元データを貯めるバッファ配列
    private var tempAudioBuffers: [AVAudioPCMBuffer] = []
    
    @Published var recognizedText: String = ""
    @Published var aiResponseText: String = ""
    @Published var isRecording: Bool = false
    @Published var isSpeaking: Bool = false
    
    //  設定画面UIから操作するためのコントロール用変数群
    @Published var isStereoMode: Bool = true       // ステレオ切り替え
    @Published var volumeMultiplier: Double = 30000.0 // ボリューム（最大60000程度。デフォルトは標準値）
    @Published var pitchRate: Float = 1.0          // 音のピッチ倍率（0.5 〜 2.0）
    @Published var selectedVoiceIdentifier: String = "" // 選択された声の識別コード
    @Published var aiMode: String = "ノーマル"       // AIのキャラクターモード
    @Published var availableVoices: [AVSpeechSynthesisVoice] = [] // iPhoneが持っている日本語音声リスト
    @Published var bleIntervalLevel: Int = 2
    
    var onSpeechRecognized: ((String) -> Void)?
    
    override init() {
        super.init()
        synthesizer.delegate = self
    }
    
    func setup(bleManager: BLEManager) {
        self.bleManager = bleManager
        self.speechRecognizer?.delegate = self
        
        SFSpeechRecognizer.requestAuthorization { status in
            print(">>> 音声認識権限ステータス: \(status)")
        }
        
        // 起動時にiPhone内に登録されている日本語の音声一覧を取得する
        fetchAvailableVoices()
    }
    
    // 日本語の話者リストを取得して初期選択するメソッド
    func fetchAvailableVoices() {
        let allVoices = AVSpeechSynthesisVoice.speechVoices()
        self.availableVoices = allVoices.filter { $0.language == "ja-JP" }
        if let firstVoice = self.availableVoices.first {
            self.selectedVoiceIdentifier = firstVoice.identifier
        }
    }
    
    func startRecording() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .duckOthers])
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("❌ 録音セッションの起動に失敗: \(error)")
        }
        
        guard !audioEngine.isRunning else { return }
        
        recognizedText = ""
        isRecording = true
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        recognitionRequest.shouldReportPartialResults = true
        
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }
        
        audioEngine.prepare()
        try? audioEngine.start()
        
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }
            if let result = result {
                self.recognizedText = result.bestTranscription.formattedString
                if result.isFinal {
                    self.stopRecording()
                    self.onSpeechRecognized?(self.recognizedText)
                }
            }
            if error != nil {
                self.stopRecording()
            }
        }
    }
    
    func stopRecording() {
        guard audioEngine.isRunning else { return }
        audioEngine.inputNode.removeTap(onBus: 0)
        audioEngine.stop()
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        isRecording = false
    }
    
    func speakAndStream(text: String) {
        guard let ble = bleManager, ble.isConnected else {
            print(">>> ロボットが未接続のためストリーミングできません")
            return
        }
        // 🔧 セッション設定を再度確認
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .measurement,
                                    options: [.defaultToSpeaker, .duckOthers])
            try session.setActive(true)
        } catch {
            print("❌ オーディオセッション設定エラー: \(error)")
        }
        
        var processedText = text
        switch aiMode {
        case "ツンデレ":
            processedText = text + "、なんだからね！"
        case "ロボット風":
            processedText = text + "。ピッ。ポッ。"
        case "やさしい":
            processedText = "えっとね、" + text + "だよ。"
        default:
            processedText = text
        }
        
        aiResponseText = processedText
        isSpeaking = true
        tempAudioBuffers.removeAll()
        
        let utterance = AVSpeechUtterance(string: processedText)
        
        // 設定画面で選ばれた声のIDを割り当てる
        if let specificVoice = AVSpeechSynthesisVoice(identifier: selectedVoiceIdentifier) {
            utterance.voice = specificVoice
        } else {
            utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        }
        
        // 設定画面から指定されたピッチ倍率（0.5〜2.0）をセット
        utterance.pitchMultiplier = pitchRate
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate  // 標準速度に
        
        //  1. コールバック内では遅延を入れず、バッファを貯めるだけにする
        synthesizer.write(utterance) { [weak self] (buffer: AVAudioBuffer) in
            guard let self = self, let pcmBuffer = buffer as? AVAudioPCMBuffer else { return }
            self.tempAudioBuffers.append(pcmBuffer)
        }
    }
    
    // バッファ取得が完了したら送信処理を開始
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.processAndSendBuffers()
        }
        DispatchQueue.main.async { [weak self] in
            self?.isSpeaking = false
        }
    }
    
    private func processAndSendBuffers() {
        var allConvertedData = Data()
            
        for pcmBuffer in tempAudioBuffers {
            guard let floatChannels = pcmBuffer.floatChannelData else { continue }
            let frameCount = Int(pcmBuffer.frameLength)
            
            // 明確に0番目のモノラルchポインタを抽出
            let channelData = floatChannels[0]

            // iOSが内部生成した元のサンプリングレート（22050Hz等）を取得
            let sourceSampleRate = pcmBuffer.format.sampleRate
            let targetSampleRate: Double = 16000.0
            
            var int16Samples = [Int16]()
            // 変換後の予測サイズで領域をあらかじめ確保（ステレオの場合は最大2倍になるため領域を広く取る）
            let capacityMultiplier = isStereoMode ? 2 : 1
            int16Samples.reserveCapacity(Int(Double(frameCount) * (targetSampleRate / sourceSampleRate)) * capacityMultiplier)
            
            let step = sourceSampleRate / targetSampleRate
            var sourceIndex = 0.0
            
            // 1chのデータを安全に16kHzへ直撃ダウンサンプリング
            while sourceIndex < Double(frameCount) {
                let idx = Int(sourceIndex)
                if idx >= frameCount { break }
                
//＜パターン１
//                // 線形補間で高品質化
//                let frac = sourceIndex - Double(idx)
//                let nextIdx = min(idx + 1, frameCount - 1)
//                let sample1 = Double(channelData[idx])
//                let sample2 = Double(channelData[nextIdx])
//                let interpolated = sample1 + (sample2 - sample1) * frac
//
//                let volumeFactor = self.volumeMultiplier / 32767.0
//                let rawSample = interpolated * volumeFactor * 32767.0
//                let int16Sample = Int16(max(-32768, min(32767, rawSample)))
//
//                // ステレオ/モノラル処理...
//                sourceIndex += step
//パターン１＞
//＜パターン２

                let floatSample = channelData[idx]

                // 🛠️ 【音量 ＆ 音割れガード倍率】
                // 画面スライダーから取得した変数を適用
                let normalizedSample = Double(floatSample)  // -1.0 ～ 1.0 の範囲
                let volumeFactor = min(self.volumeMultiplier / 32767.0, 2.0)  // 最大2.0倍に制限
                let rawSample = normalizedSample * volumeFactor * 32767.0

                let int16Sample = Int16(max(-32768, min(32767, rawSample)))

                // 【モノラル / ステレオ切り替え機能の反映】
                if self.isStereoMode {
                    // ステレオモード：LとRのチャンネルへ交互に同じデータを連続して2個詰める
                    int16Samples.append(int16Sample) // L
                    int16Samples.append(int16Sample) // R
                } else {
                    // モノラルモード：元の通り1個だけ詰める
                    int16Samples.append(int16Sample) // モノラル
                }
                sourceIndex += step
//パターン２＞
            }
            
            // リトルエンディアンでバイナリ化
            for sample in int16Samples {
                var leSample = sample.littleEndian
                withUnsafeBytes(of: &leSample) { allConvertedData.append(contentsOf: $0) }
            }
        }
            
        if allConvertedData.isEmpty {
            print("❌ 音声データが構築されませんでした")
            DispatchQueue.main.async { [weak self] in
                self?.isSpeaking = false
            }
            return
        }
            
        print("🚀 [送信開始] 総バイナリサイズ: \(allConvertedData.count) bytes。ESP32へストリーム投下します。")
            
        let totalLength = allConvertedData.count
        var offset = 0
            
        while offset < totalLength {
            let chunkSize = min(self.packetSize, totalLength - offset)
            let chunk = allConvertedData.subdata(in: offset..<(offset + chunkSize))
            
            DispatchQueue.main.async { [weak self] in
                self?.bleManager?.sendVoicePacket(audioData: chunk)
            }
                
            offset += chunkSize
            
            // OS（iPhone）のBluetooth通信の仕様上、これらのウエイト値は
            //「1250マイクロ秒（1.25ms）」の倍数に設定する
            // ステレオ時はデータが2倍なので、モノラルのウエイトを半分にして超高速で送り込む。
            let baseInterval = self.bleIntervalLevel * 1250
            
            if self.isStereoMode {
                // ステレオの場合：設定値 ✕ 1250
                usleep(useconds_t(baseInterval))
            } else {
                // モノラルの場合：（設定値 ✕ 1250）✕ 2
                usleep(useconds_t(baseInterval * 2))
            }
        }
            
        print("✅ [ストリーミング送信完了]")
        DispatchQueue.main.async { [weak self] in
            self?.isSpeaking = false
        }
    }
}
