// =========================================================================
// File: iOSApp/BLEManager.swift
// Description: iRobapp-mini用 BLEセントラルマネージャー（修正版）
// =========================================================================

import Foundation
import CoreBluetooth
import Combine

class BLEManager: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    private var centralManager: CBCentralManager!
    private var connectedPeripheral: CBPeripheral?
    
    private let serviceUUID = CBUUID(string: "4fafc201-1fb5-459e-8fcc-c5c9c331914b")
    private let eyeCharacteristicUUID = CBUUID(string: "beb5483e-36e1-4688-b7f5-ea07361b26a8")
    private let voiceCharacteristicUUID = CBUUID(string: "d0d34192-3eb6-41fb-a15c-0e24177c34dd")
    
    private var eyeCharacteristic: CBCharacteristic?
    private var voiceCharacteristic: CBCharacteristic?
    
    @Published var discoveredPeripherals: [CBPeripheral] = []
    @Published var isConnected: Bool = false
    @Published var connectedDeviceName: String = "未接続"
    
    override init() {
        super.init()
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }
    
    func startScanning() {
        discoveredPeripherals.removeAll()
        if centralManager.state == .poweredOn {
            centralManager.scanForPeripherals(withServices: [serviceUUID], options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
            print(">>> BLEスキャンを開始しました...")
        }
    }
    
    func stopScanning() {
        centralManager.stopScan()
    }
    
    func connect(to peripheral: CBPeripheral) {
        stopScanning()
        connectedPeripheral = peripheral
        connectedPeripheral?.delegate = self
        centralManager.connect(peripheral, options: nil)
    }
    
    func disconnect() {
        if let peripheral = connectedPeripheral {
            centralManager.cancelPeripheralConnection(peripheral)
        }
    }
    
    func sendEyePosition(yValue: Int) {
        guard let peripheral = connectedPeripheral, let char = eyeCharacteristic else { return }
        let data = String(yValue).data(using: .utf8)!
        peripheral.writeValue(data, for: char, type: .withResponse)
    }
    
    func sendVoicePacket(audioData: Data) {
        guard let peripheral = connectedPeripheral, let char = voiceCharacteristic else { return }
        peripheral.writeValue(audioData, for: char, type: .withoutResponse)
    }
    
    // MARK: - CBCentralManagerDelegate
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            startScanning()
        } else {
            print(">>> Bluetoothがオフか利用できません。")
        }
    }
    
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi RSSI: NSNumber) {
        if !discoveredPeripherals.contains(where: { $0.identifier == peripheral.identifier }) {
            discoveredPeripherals.append(peripheral)
            print(">>> 発見: \(peripheral.name ?? "Unknown")")
        }
    }
    
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        isConnected = true
        connectedDeviceName = peripheral.name ?? "iRobapp-mini"
        print(">>> ロボットと接続成功！サービスを探索します。")
        peripheral.discoverServices([serviceUUID])
    }
    
    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        isConnected = false
        print(">>> 接続失敗: \(error?.localizedDescription ?? "")")
        startScanning()
    }
    
    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        isConnected = false
        connectedDeviceName = "未接続"
        print(">>> 接続が切断されました。再スキャンを再開します。")
        startScanning()
    }
    
    // MARK: - CBPeripheralDelegate
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }
        for service in services {
            if service.uuid == serviceUUID {
                // 【修正】service ではなく peripheral.discoverCharacteristics を呼び出す
                peripheral.discoverCharacteristics([eyeCharacteristicUUID, voiceCharacteristicUUID], for: service)
            }
        }
    }
    
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard let characteristics = service.characteristics else { return }
        for char in characteristics {
            if char.uuid == eyeCharacteristicUUID {
                eyeCharacteristic = char
            } else if char.uuid == voiceCharacteristicUUID {
                voiceCharacteristic = char
            }
        }
        print(">>> キャラクタリスティクスの紐付けが完了しました。")
    }
}

