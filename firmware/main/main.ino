// =========================================================================
// File: firmware/main/main.ino 
// Description: iRobapp-mini メイン制御ファームウェア（iOS接続安定化モデル）
// Spec: 接続パラメータ最適化による切断防止、MACアドレス下4桁による個別アドバタイズ
//       瞳物理演算、LovyanGFX描画、setup()でのMACアドレス個別広告、自動復旧ループ
// =========================================================================

#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <ESP32Servo.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// -------------------------------------------------------------------------
// 1. BLE通信のUUIDおよびパラメータ設定（iOS接続維持のための重要セッティング）
// -------------------------------------------------------------------------
#define SERVICE_UUID           "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_EYE_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHARACTERISTIC_VOICE_UUID "d0d34192-3eb6-41fb-a15c-0e24177c34dd"

BLEServer* pServer = nullptr;
BLECharacteristic* pEyeCharacteristic = nullptr;
BLECharacteristic* pVoiceCharacteristic = nullptr;

bool deviceConnected = false;
bool oldDeviceConnected = false;

// -------------------------------------------------------------------------
// 2. LovyanGFX 液晶初期化設定 (GC9A01専用カスタムクラス)
// -------------------------------------------------------------------------
class LGFX_iRobapp : public lgfx::LGFX_Device {
  lgfx::Panel_GC9A01 _panel_instance;
  lgfx::Bus_SPI      _bus_instance;

public:
  LGFX_iRobapp() {
    auto cfg = _bus_instance.config();
    cfg.spi_host = SPI2_HOST;
    cfg.spi_mode = 0;
    cfg.freq_write = 40000000; // 画面のチラつきを防ぐ40MHz爆速転送
    cfg.pin_sclk = 10;         // シルク D10 -> GPIO 10
    cfg.pin_mosi = 8;          // シルク D8  -> GPIO 8
    cfg.pin_miso = -1;
    cfg.pin_dc   = 3;          // シルク D2  -> GPIO 3
    _bus_instance.config(cfg);
    _panel_instance.setBus(&_bus_instance);

    auto p_cfg = _panel_instance.config();
    p_cfg.pin_cs           = 4;   // シルク D3  -> GPIO 4
    p_cfg.pin_rst          = 2;   // シルク D1  -> GPIO 2
    p_cfg.panel_width      = 240;
    p_cfg.panel_height     = 240;
    p_cfg.offset_x         = 0;
    p_cfg.offset_y         = 0;
    p_cfg.invert           = true;
    p_cfg.rgb_order        = false;
    _panel_instance.config(p_cfg);
    setPanel(&_panel_instance);
  }
};

LGFX_iRobapp lcd;
LGFX_Sprite canvas(&lcd);

// ---------------------------------------------------------
// 3. ピン定義 & グローバル変数
// ---------------------------------------------------------
const int PIN_SERVO_PAN  = 5;   // シルク D4 -> GPIO 5
const int PIN_SERVO_TAIL = 6;   // シルク D5 -> GPIO 6

Servo servoPan;
Servo servoTail;

// 瞳のアニメーション変数
float eyeY = 120.0;
float targetEyeY = 120.0;
const float eyeX = 120.0;
const float eyeRadius = 45.0;
const float whiteRadius = 95.0;

unsigned long lastBlinkTime = 0;
unsigned long blinkInterval = 3000;
bool isBlinking = false;
float blinkProgress = 0.0;
bool isSleepMode = false;
unsigned long lastInteractionTime = 0;
const unsigned long SLEEP_TIMEOUT = 30000; // 30秒

// -------------------------------------------------------------------------
// 4. BLEサーバー・接続状態コールバック (切断防止ロジック)
// -------------------------------------------------------------------------
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer, esp_ble_gatts_cb_param_t *param) {
        deviceConnected = true;
        lastInteractionTime = millis();
        isSleepMode = false;
        
        // 【核心：切断対策】iOSが要求する最適な通信タイミング（Connection Interval）を強制設定
        pServer->updateConnParams(param->connect.remote_bda, 12, 24, 0, 400);
        Serial.println(">>> iPhoneとガッチリ接続されました！");
    };

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println(">>> iPhoneとの接続が切れました。広告を再開します。");
    }
};

// 👁️ 目の制御用データ受信コールバック
class EyeCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        std::string value = pCharacteristic->getValue();
        if (value.length() > 0) {
            lastInteractionTime = millis();
            isSleepMode = false;
            int receivedY = (int)value[0]; 
            if(value.length() > 2) receivedY = atoi(value.c_str());
            targetEyeY = (float)receivedY;
            Serial.printf("Eye Y目標更新: %f\n", targetEyeY);
        }
    }
};

// 🔊 音声ストリーミングデータ受信コールバック
class VoiceCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        std::string value = pCharacteristic->getValue();
        if (value.length() > 0) {
            lastInteractionTime = millis();
            isSleepMode = false;
            
            // ★音声データ（パケット）の受け取り口
            // 将来ここにI2S再生バッファへの流し込みを記述します。
            
            // 話しかけられたトリガー動作：尻尾を2回キュキュッと振る
            static unsigned long lastTailTrigger = 0;
            if (millis() - lastTailTrigger > 3000) { 
                for(int i=0; i<2; i++) {
                    servoTail.write(120); delay(120);
                    servoTail.write(60);  delay(120);
                }
                servoTail.write(90);
                lastTailTrigger = millis();
            }
        }
    }
};

// -------------------------------------------------------------------------
// 5. 描画・物理演算ロジック（ヌルヌル動く視線移動とまばたき）
// -------------------------------------------------------------------------
void updateEyePhysics() {
  if (isSleepMode) {
    if (blinkProgress < 1.0f) blinkProgress += 0.05f; // スリープ時はまぶたをゆっくり閉じる
    return;
  }
  
  // 視線のヌルヌル追従計算（イージング）
  eyeY += (targetEyeY - eyeY) * 0.15f; 

  // まばたきアニメーションの進行管理
  if (!isBlinking) {
    if (millis() - lastBlinkTime > blinkInterval) {
      isBlinking = true;
      blinkProgress = 0.0f;
    }
  } else {
    blinkProgress += 0.25f; // まばたき速度
    if (blinkProgress >= 2.0f) { // 往復（閉じて開く）完了
      isBlinking = false;
      lastBlinkTime = millis();
      
      // 3パターンの時間間隔を乱数で決定（要件定義通り）
      int pattern = random(0, 3);
      if (pattern == 0) blinkInterval = 2000;      // 2秒
      else if (pattern == 1) blinkInterval = 4000; // 4秒
      else blinkInterval = 6000;                   // 6秒
    }
  }
}

void drawEye() {
  canvas.clear(TFT_BLACK);
  
  // ① 白目の描画
  canvas.fillCircle(120, 120, whiteRadius, TFT_WHITE);

  // ② 黒目（瞳）の描画
  if (blinkProgress < 1.0f) {
    float currentY = eyeY;
    canvas.fillCircle(eyeX, currentY, eyeRadius, TFT_BLACK);
    // キラキラ（ハイライト）を入れて生命感を演出
    canvas.fillCircle(eyeX - 12, currentY - 12, 10, TFT_WHITE);
  }

  // ③ まぶたの描画（上下から閉じるリアルな演算）
  float currentProgress = (blinkProgress > 1.0f) ? (2.0f - blinkProgress) : blinkProgress;
  if (currentProgress > 0.0f) {
    int lidHeight = (int)(120 * currentProgress);
    canvas.fillRect(0, 0, 240, lidHeight, TFT_BLACK);         // 上まぶた
    canvas.fillRect(0, 240 - lidHeight, 240, lidHeight, TFT_BLACK); // 下まぶた
  }
  
  // チラつきを100%防ぐダブルバッファ転送
  canvas.pushSprite(0, 0);
}

// -------------------------------------------------------------------------
// 6. 起動セットアップ（MACアドレス下4桁を自動取得して個別広告）
// -------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0));

  // 液晶 initialization
  lcd.init();
  canvas.createSprite(240, 240);
  
  // サーボモーターの初期設定
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  servoPan.setPeriodHertz(50);
  servoTail.setPeriodHertz(50);
  servoPan.attach(PIN_SERVO_PAN, 500, 2400);
  servoTail.attach(PIN_SERVO_TAIL, 500, 2400);
  servoPan.write(90); // 正面を向く
  servoTail.write(90); // 尻尾をまっすぐに

  // --- 【複数ロボット識別対策】MACアドレスの取得と、個別ID付き広告の起動 ---
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA); // チップ固有のMACアドレスを読み出す
  
  // 下4桁（末尾の2バイト分）を16進数の文字列に変換 (例: mac[4]=0xAB, mac[5]=0x3F -> "AB3F")
  char robotName[32];
  sprintf(robotName, "iRobapp-mini-%02X%02X", mac[4], mac[5]);
  Serial.printf(">>> デバイス名を確定しました: %s\n", robotName);

  // BLEデバイスの初期化
  BLEDevice::init(robotName);

  // BLEサーバーの作成
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // BLEサービスの作成
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // 👁️ 目の制御用キャラクタリスティクス (Write)
  pEyeCharacteristic = pService->createCharacteristic(
                         CHARACTERISTIC_EYE_UUID,
                         BLECharacteristic::PROPERTY_WRITE
                       );
  pEyeCharacteristic->setCallbacks(new EyeCallbacks());

  // 🔊 音声ストリーミング用キャラクタリスティクス (Write / Notify)
  pVoiceCharacteristic = pService->createCharacteristic(
                          CHARACTERISTIC_VOICE_UUID,
                          BLECharacteristic::PROPERTY_WRITE  |
                          BLECharacteristic::PROPERTY_NOTIFY
                        );
  pVoiceCharacteristic->setCallbacks(new VoiceCallbacks());
  pVoiceCharacteristic->addDescriptor(new BLE2902());

  // サービスの開始
  pService->start();

  // アドバタイズ（電波の発信）開始設定
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // iOS接続切断対策用のヒントパラメータ
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  
  Serial.println(">>> BLEアドバタイズを開始しました。iPhoneからの接続を待っています...");
  lastBlinkTime = millis();
  lastInteractionTime = millis();
}

// -------------------------------------------------------------------------
// 7. メインループ（自動再接続復旧、自律ランダムモーションの統合）
// -------------------------------------------------------------------------
void loop() {
  // BLEの切断後・再接続時の自動アドバタイズ再開処理（完全自動復旧システム）
  if (!deviceConnected && oldDeviceConnected) {
      delay(500); // 接続が完全に切れるのを待つ
      pServer->startAdvertising(); // 電波広告を自動で再開！
      Serial.println(">>> アドバタイズを自動再開しました。再接続を待機中...");
      oldDeviceConnected = deviceConnected;
  }
  if (deviceConnected && !oldDeviceConnected) {
      oldDeviceConnected = deviceConnected;
  }

  // 自律動作：しばらく操作がない場合、自動でスリープモードに移行して瞳を閉じる
  if (millis() - lastInteractionTime > SLEEP_TIMEOUT) {
    isSleepMode = true;
  }

  // 自律動作：モードに応じた乱数ベースの不定期な首振りと尻尾振り演出（要件定義通り）
  if (!isSleepMode && random(0, 1000) < 3) { // 約10秒に数回の確率で発生
    servoPan.write(random(60, 120));          // 首を左右にきょろきょろ
    if(random(0, 2) == 0) {
      servoTail.write(110); delay(100);       // 尻尾をフリフリ
      servoTail.write(70);  delay(100);
      servoTail.write(90);
    }
  }

  // 物理演算の更新 ＆ 液晶画面のリフレッシュ
  updateEyePhysics();
  drawEye();

  delay(16); // 秒間約60フレーム(60fps)の超滑らかなテンポを維持
}
