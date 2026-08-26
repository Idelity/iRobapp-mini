// =========================================================================
// File: iOSApp/VoicePipelineManager.swift
// Description: iRobapp-mini用 音声認識(STT) ＆ リアルタイム音声ストリーミング(TTS)
// =========================================================================

import Foundation
import Speech
import AVFoundation
import Combine

class VoicePipelineManager: NSObject, ObservableObject, SFSpeechRecognizerDelegate {
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
    
    var onSpeechRecognized: ((String) -> Void)?
    
    func setup(bleManager: BLEManager) {
        self.bleManager = bleManager
        self.speechRecognizer?.delegate = self
        
        SFSpeechRecognizer.requestAuthorization { status in
            print(">>> 音声認識権限ステータス: \(status)")
        }
    }
    
    func startRecording() {
        // 録音を始める前に、セッションを録音モード（PlayAndRecord）に戻す
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker])
            try session.setActive(true)
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
        
        aiResponseText = text
        isSpeaking = true
        tempAudioBuffers.removeAll()
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.rate = 0.5
        
        // 🌟 1. コールバック内では遅延を入れず、バッファを貯めるだけにする
        synthesizer.write(utterance) { [weak self] (buffer: AVAudioBuffer) in
            guard let self = self, let pcmBuffer = buffer as? AVAudioPCMBuffer else { return }
            self.tempAudioBuffers.append(pcmBuffer)
        }
        
        // 🌟 2. 音声生成が終わるのを待ってから、別スレッドで安全に送信する
        let delayTime = Double(text.count) * 0.2 + 0.6
        DispatchQueue.main.asyncAfter(deadline: .now() + delayTime) { [weak self] in
            // 🌟 ベースとなるselfを安全にアンラップ
            guard let self = self else { return }
            
            if self.tempAudioBuffers.isEmpty {
                self.isSpeaking = false
                return
            }
            
            // バックグラウンドでデータを一括処理して送信
            DispatchQueue.global(qos: .userInitiated).async {
                self.processAndSendBuffers()
            }
            
            // 🌟 UIスレッド（メイン）に戻してフラグをオフにする
            DispatchQueue.main.async {
                self.isSpeaking = false
            }
        }
    }
    
    private func processAndSendBuffers() {
        var allConvertedData = Data()
            
        for pcmBuffer in tempAudioBuffers {
            guard let floatChannels = pcmBuffer.floatChannelData else { continue }
            let frameCount = Int(pcmBuffer.frameLength)
            
            // 🌟明確に0番目のモノラルchポインタを抽出
            let channelData = floatChannels[0]
            
            // iOSが内部生成した元のサンプリングレート（22050Hz等）を取得
            let sourceSampleRate = pcmBuffer.format.sampleRate
            let targetSampleRate: Double = 16000.0 // 🎯マイコン側に完全同期
            
            var int16Samples = [Int16]()
            // 変換後の予測サイズで領域をあらかじめ確保
            int16Samples.reserveCapacity(Int(Double(frameCount) * (targetSampleRate / sourceSampleRate)))
            
            let step = sourceSampleRate / targetSampleRate
            var sourceIndex = 0.0
            
            // 🌟 【ここを最適化】1chのデータを安全に16kHzへ直撃ダウンサンプリング
            while sourceIndex < Double(frameCount) {
                let idx = Int(sourceIndex)
                if idx >= frameCount { break }
                
                let floatSample = channelData[idx]
                
                // 🛠️ 【音量 ＆ 音割れガード倍率】
                // ハンダ全廃構成のスピーカーで最もクリアに鳴る「120.0」に固定します
                let volumeMultiplier = 120.0
                let rawSample = Double(floatSample) * volumeMultiplier
                
                let int16Sample = Int16(max(-32768, min(32767, rawSample)))
                int16Samples.append(int16Sample)
                
                sourceIndex += step
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
            // 16kHzストリームに対して、180バイト(約5.6ms分の音声)を「4msウェイト」で
            // 送信バッファが絶対に枯渇しない理想の間隔でストリーミングします
            usleep(4000)
        }
            
        print("✅ [ストリーミング送信完了]")
        
        DispatchQueue.main.async { [weak self] in
            self?.isSpeaking = false
        }
    }
}
