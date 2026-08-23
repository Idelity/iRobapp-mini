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
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        
        synthesizer.write(utterance) { [weak self] (buffer: AVAudioBuffer) in
            guard let self = self else { return }
            guard let pcmBuffer = buffer as? AVAudioPCMBuffer else { return }
            guard let floatChannels = pcmBuffer.floatChannelData else { return }
            
            let frameCount = Int(pcmBuffer.frameLength)
            // 【修正】チャンネルのポインタ配列から先頭チャンネル（0番目）のデータを取り出す
            let channelData = floatChannels[0]
            
            var audioBytes = [Float32]()
            for i in 0..<frameCount {
                audioBytes.append(channelData[i])
            }
            
            let rawData = Data(bytes: audioBytes, count: audioBytes.count * MemoryLayout<Float32>.size)
            
            let packetSize = 480
            var offset = 0
            while offset < rawData.count {
                let chunkSize = min(packetSize, rawData.count - offset)
                let chunk = rawData.subdata(in: offset..<(offset + chunkSize))
                
                self.bleManager?.sendVoicePacket(audioData: chunk)
                offset += chunkSize
                
                usleep(5000)
            }
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + Double(text.count) * 0.2 + 1.0) {
            self.isSpeaking = false
        }
    }
}

