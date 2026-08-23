// =========================================================================
// File: iOSApp/ContentView.swift
// Description: ロボット選択・接続ステータス表示のSwiftUIビュー
// =========================================================================

import SwiftUI
import CoreBluetooth

struct ContentView: View {
    @StateObject private var bleManager = BLEManager()
    
    var body: some View {
        NavigationView {
            VStack {
                // 接続ステータスカード
                VStack(spacing: 8) {
                    Circle()
                        .fill(bleManager.isConnected ? Color.green : Color.red)
                        .frame(width: 16, height: 16)
                    Text(bleManager.connectedDeviceName)
                        .font(.headline)
                    Text(bleManager.isConnected ? "安定接続中（切断保護有効）" : "近くのロボットをスキャン中...")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)
                
                // 発見されたロボットリスト
                List(bleManager.discoveredPeripherals, id: \.identifier) { peripheral in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(peripheral.name ?? "iRobapp-mini")
                                .font(.body)
                                .fontWeight(.semibold)
                            Text(peripheral.identifier.uuidString)
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                        Spacer()
                        Button("接続") {
                            bleManager.connect(to: peripheral)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .refreshable {
                    bleManager.startScanning()
                }
                
                // 動作テスト用ボタン（接続時のみ有効）
                if bleManager.isConnected {
                    HStack(spacing: 16) {
                        Button("上を向く") { bleManager.sendEyePosition(yValue: 60) }
                            .buttonStyle(.bordered)
                        Button("正面") { bleManager.sendEyePosition(yValue: 120) }
                            .buttonStyle(.bordered)
                        Button("下を向く") { bleManager.sendEyePosition(yValue: 180) }
                            .buttonStyle(.bordered)
                    }
                    .padding()
                    
                    Button("切断する") {
                        bleManager.disconnect()
                    }
                    .foregroundColor(.red)
                    .padding(.bottom)
                }
            }
            .navigationTitle("iRobapp コントローラー")
            .onAppear {
                bleManager.startScanning()
            }
        }
    }
}
