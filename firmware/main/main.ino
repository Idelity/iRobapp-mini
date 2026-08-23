// =========================================================================
// File: firmware/main/main.ino
// Description: iRobapp-mini メイン制御ファームウェア（最新環境完全対応版）
// Spec: WiFi.macAddressによる安全な固有ID広告、最新ESP32コア対応BLE・液晶・サーボ
// =========================================================================

#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// -------------------------------------------------------------------------
// 1. BLE通信のUUIDおよびパラメータ設定
// -------------------------------------------------------------------------
#define SERVICE_UUID            "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
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
    cfg.freq_write = 40000000;
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

// -------------------------------------------------------------------------
// 3. ピン定義 & グローバル変数
// -------------------------------------------------------------------------
const int PIN_SERVO_PAN  = 5;   // シルク D4 -> GPIO 5
const int PIN_SERVO_TAIL = 6;   // シルク D5 -> GPIO 6

Servo servoPan;
Servo servoTail;

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
const unsigned long SLEEP_TIMEOUT = 30000;

// -------------------------------------------------------------------------
// 4. BLEサーバー・接続状態コールバック
// -------------------------------------------------------------------------
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        lastInteractionTime = millis();
        isSleepMode = false;
        Serial.println(">>> iPhoneと接続されました！");
    };

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println(">>> iPhoneとの接続が切れました。広告を再開します。");
    }
};

// 👁️ 目の制御用データ受信コールバック
class EyeCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String value = pCharacteristic->getValue();
        if (value.length() > 0) {
            lastInteractionTime = millis();
            isSleepMode = false;
            targetEyeY = value.toFloat();
            Serial.printf("Eye Y目標更新: %f\n", targetEyeY);
        }
    }
};

// 🔊 音声ストリーミングデータ受信コールバック
class VoiceCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String value = pCharacteristic->getValue();
        if (value.length() > 0) {
            lastInteractionTime = millis();
            isSleepMode = false;
            
            // トリガー動作：音声パケット受信時に尻尾を2回振る
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
// 5. 描画・物理演算ロジック
// -------------------------------------------------------------------------
void updateEyePhysics() {
  if (isSleepMode) {
    if (blinkProgress < 1.0f) blinkProgress += 0.05f;
    return;
  }
  eyeY += (targetEyeY - eyeY) * 0.15f; 

  if (!isBlinking) {
    if (millis() - lastBlinkTime > blinkInterval) {
      isBlinking = true;
      blinkProgress = 0.0f;
    }
  } else {
    blinkProgress += 0.25f;
    if (blinkProgress >= 2.0f) {
      isBlinking = false;
      lastBlinkTime = millis();
      int pattern = random(0, 3);
      if (pattern == 0) blinkInterval = 2000;
      else if (pattern == 1) blinkInterval = 4000;
      else blinkInterval = 6000;
    }
  }
}

void drawEye() {
  canvas.clear(TFT_BLACK);
  canvas.fillCircle(120, 120, whiteRadius, TFT_WHITE);

  if (blinkProgress < 1.0f) {
    canvas.fillCircle(eyeX, eyeY, eyeRadius, TFT_BLACK);
    canvas.fillCircle(eyeX - 12, eyeY - 12, 10, TFT_WHITE);
  }

  float currentProgress = (blinkProgress > 1.0f) ? (2.0f - blinkProgress) : blinkProgress;
  if (currentProgress > 0.0f) {
    int lidHeight = (int)(120 * currentProgress);
    canvas.fillRect(0, 0, 240, lidHeight, TFT_BLACK);
    canvas.fillRect(0, 240 - lidHeight, 240, lidHeight, TFT_BLACK);
  }
  canvas.pushSprite(0, 0);
}

// -------------------------------------------------------------------------
// 6. 起動セットアップ
// -------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0));

  lcd.init();
  canvas.createSprite(240, 240);
  
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  servoPan.setPeriodHertz(50);
  servoTail.setPeriodHertz(50);
  servoPan.attach(PIN_SERVO_PAN, 500, 2400);
  servoTail.attach(PIN_SERVO_TAIL, 500, 2400);
  servoPan.write(90);
  servoTail.write(90);

  // WiFiのMACアドレスから下4桁を取得して固有デバイス名を生成
  WiFi.mode(WIFI_MODE_STA);
  String macStr = WiFi.macAddress();
  macStr.replace(":", "");
  String macSuffix = macStr.substring(macStr.length() - 4);
  String deviceName = "iRobapp-mini-" + macSuffix;
  
  Serial.printf(">>> デバイス名を確定しました: %s\n", deviceName.c_str());

  BLEDevice::init(deviceName.c_str()); 
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pEyeCharacteristic = pService->createCharacteristic(
                         CHARACTERISTIC_EYE_UUID,
                         BLECharacteristic::PROPERTY_WRITE
                       );
  pEyeCharacteristic->setCallbacks(new EyeCallbacks());

  pVoiceCharacteristic = pService->createCharacteristic(
                          CHARACTERISTIC_VOICE_UUID,
                          BLECharacteristic::PROPERTY_WRITE  |
                          BLECharacteristic::PROPERTY_NOTIFY
                        );
  pVoiceCharacteristic->setCallbacks(new VoiceCallbacks());
  pVoiceCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  
  Serial.println(">>> BLEアドバタイズ中...");
  lastBlinkTime = millis();
  lastInteractionTime = millis();
}

// -------------------------------------------------------------------------
// 7. メメインループ
// -------------------------------------------------------------------------
void loop() {
  if (!deviceConnected && oldDeviceConnected) {
      delay(500);
      pServer->startAdvertising();
      oldDeviceConnected = deviceConnected;
  }
  if (deviceConnected && !oldDeviceConnected) {
      oldDeviceConnected = deviceConnected;
  }

  if (millis() - lastInteractionTime > SLEEP_TIMEOUT) {
    isSleepMode = true;
  }

  if (!isSleepMode && random(0, 1000) < 3) {
    servoPan.write(random(60, 120));
    if(random(0, 2) == 0) {
      servoTail.write(110); delay(100);
      servoTail.write(70);  delay(100);
      servoTail.write(90);
    }
  }

  updateEyePhysics();
  drawEye();
  delay(16);
}
