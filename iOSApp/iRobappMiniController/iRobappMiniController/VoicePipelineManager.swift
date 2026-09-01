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
    @Published var isStereoMode: Bool = false       // ステレオ切り替え
    @Published var volumeMultiplier: Double = 40000.0 // ボリューム（最大60000程度。デフォルトは標準値）
    @Published var pitchRate: Float = 1.0          // 音のピッチ倍率（0.5 〜 2.0）
    @Published var selectedVoiceIdentifier: String = "" // 選択された声の識別コード
    @Published var aiMode: String = "ノーマル"       // AIのキャラクターモード
    @Published var availableVoices: [AVSpeechSynthesisVoice] = [] // iPhoneが持っている日本語音声リスト
    @Published var bleIntervalLevel: Int = 2
    @Published var targetRMS: Double = 0.18
    @Published var maxGain: Double = 18.0
    @Published var limiterScale: Double = 2.0  // 今は2.0で効果ありとのこと
    private var previousGain: Double = 1.0     // 平滑化用
    private let smoothingAlpha: Double = 0.1  // 0.0..1.0 (小さいほどゆっくり)
    
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
        //recognitionTask?.cancel()
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
            guard let self = self else { return }
            guard let pcmBuffer = buffer as? AVAudioPCMBuffer else { return }

            // フレームが 0 のバッファはログだけ出してスキップ（終端マーカー的なケースもある）
            let frameCount = Int(pcmBuffer.frameLength)
            if frameCount == 0 {
                print("DEBUG_TTS_WRITE: received buffer frames=0 sr=\(pcmBuffer.format.sampleRate)")
                return
            }

            // 安全な深いコピーを作る
            guard let copied = AVAudioPCMBuffer(pcmFormat: pcmBuffer.format, frameCapacity: pcmBuffer.frameCapacity) else { return }
            copied.frameLength = pcmBuffer.frameLength

            let channelCount = Int(pcmBuffer.format.channelCount)
            let bytesPerFrame = MemoryLayout<Float>.size
            if let src = pcmBuffer.floatChannelData, let dst = copied.floatChannelData {
                for ch in 0..<channelCount {
                    // バイト数: frameCount * sizeof(Float)
                    let byteCount = frameCount * bytesPerFrame
                    memcpy(dst[ch], src[ch], byteCount)
                }
            }

            // 追加ログ（任意）
            print("DEBUG_TTS_WRITE: copied buffer frames=\(frameCount) sr=\(pcmBuffer.format.sampleRate) channels=\(channelCount)")

            // 末尾に安全なコピーを追加
            self.tempAudioBuffers.append(copied)
        }
    }
    
    // バッファ取得が完了したら送信処理を開始
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        print("🎤 TTS didFinish: totalBuffers=\(tempAudioBuffers.count) utterance.speechString=\(utterance.speechString)")
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.processAndSendBuffers()
        }
        DispatchQueue.main.async { [weak self] in
            self?.isSpeaking = false
        }
    }
    private func buildAudioData(from buffers: [AVAudioPCMBuffer], targetSampleRate: Double = 16000.0) -> Data {
        var allConvertedData = Data()
        let eps = 1e-12
        
        for pcmBuffer in buffers {
            guard let floatChannels = pcmBuffer.floatChannelData else { continue }
            let frameCount = Int(pcmBuffer.frameLength)
            if frameCount == 0 { continue }
            let channelData = floatChannels[0]
            let sourceSampleRate = pcmBuffer.format.sampleRate
            
            // --- RMS / Peak 計測（入力）
            var sumSquares: Double = 0.0
            var peak: Float = 0.0
            for i in 0..<frameCount {
                let v = channelData[i]
                sumSquares += Double(v * v)
                peak = max(peak, abs(v))
            }
            let rms = sqrt(sumSquares / Double(max(1, frameCount)))
            print("🔍 pcmBuffer frames=\(frameCount) sourceSR=\(sourceSampleRate) rms=\(rms) peak=\(peak)")
            
            // --- ゲイン計算（RMSベース）
            let target = max(0.01, targetRMS)   // 下限を保証
            let currentRMS = max(rms, eps)
            var gain = target / currentRMS
            gain = min(gain, maxGain)
            
            // --- 平滑化（前バッファとの遷移を滑らかに）
            let smoothedGain = previousGain * (1.0 - smoothingAlpha) + gain * smoothingAlpha
            previousGain = smoothedGain
            
            // --- リサンプリング（線形補間）
            let step = sourceSampleRate / targetSampleRate
            var sourceIndex = 0.0
            var int16Samples = [Int16]()
            int16Samples.reserveCapacity(Int(Double(frameCount) * (targetSampleRate / sourceSampleRate)) * (isStereoMode ? 2 : 1))
            
            while sourceIndex < Double(frameCount) {
                let idx = Int(sourceIndex)
                if idx >= frameCount { break }
                let frac = sourceIndex - Double(idx)
                let nextIdx = min(idx + 1, frameCount - 1)
                let s1 = Double(channelData[idx])
                let s2 = Double(channelData[nextIdx])
                var sample = s1 + (s2 - s1) * frac
                
                // ゲイン適用
                sample *= smoothedGain
                
                // ソフトリミッタ（tanh）
                sample = tanh(sample * limiterScale)
                
                // 16bitスケール化
                let int16Val = Int16(max(-32768, min(32767, Int(round(sample * 32767.0)))))
                
                if isStereoMode {
                    int16Samples.append(int16Val)
                    int16Samples.append(int16Val)
                } else {
                    int16Samples.append(int16Val)
                }
                sourceIndex += step
            }
            
            // --- バイナリ化（リトルエンディアン）
            for sample in int16Samples {
                var leSample = sample.littleEndian
                withUnsafeBytes(of: &leSample) { allConvertedData.append(contentsOf: $0) }
            }
        }
        
        // ログ（出力全体のサイズ）
        print("🔧 buildAudioData -> totalBytes=\(allConvertedData.count)")
        return allConvertedData
    }
    
    private func processAndSendBuffers() {
        let allConvertedData = buildAudioData(from: tempAudioBuffers, targetSampleRate: 16000.0)
        
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
            
            let baseInterval = self.bleIntervalLevel * 1250
            
            if self.isStereoMode {
                usleep(useconds_t(baseInterval))
            } else {
                usleep(useconds_t(baseInterval * 2))
            }
        }
        
        print("✅ [ストリーミング送信完了]")
        DispatchQueue.main.async { [weak self] in
            self?.isSpeaking = false
        }
    }
    func testLocalTTS(text: String) {
        // AVAudioSession を整える
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [])
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            print("❌ AVAudioSession error: \(error)")
        }
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.pitchMultiplier = pitchRate
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        synthesizer.speak(utterance)
    }
    // buffers: 再生したい AVAudioPCMBuffer の配列（例: tempAudioBuffers を渡す）
    func playBuffersLocally(_ buffers: [AVAudioPCMBuffer]) {
        guard !buffers.isEmpty else { return }
        
        // 新しいエンジン＆プレイヤーノード（デバッグ用に毎回作る簡易実装）
        let engine = AVAudioEngine()
        let player = AVAudioPlayerNode()
        engine.attach(player)
        let format = buffers[0].format
        engine.connect(player, to: engine.mainMixerNode, format: format)
        
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
            try engine.start()
        } catch {
            print("❌ engine start error: \(error)")
            return
        }
        
        player.play()
        for buf in buffers {
            player.scheduleBuffer(buf, completionHandler: nil)
        }
        
        // 再生を維持するために短い遅延（デバッグ：数秒で止める）
        DispatchQueue.global().asyncAfter(deadline: .now() + 5.0) {
            player.stop()
            engine.stop()
            do {
                try AVAudioSession.sharedInstance().setActive(false)
            } catch {}
        }
    }
    // getTempBuffersForDebug
    func getTempBuffersForDebug() -> [AVAudioPCMBuffer] {
        return tempAudioBuffers
    }
}
