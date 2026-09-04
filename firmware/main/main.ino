// =========================================================================
// File: firmware/main/main.ino
// Description: iRobapp-mini メイン制御ファームウェア（ピュアモノラル直撃版）
// Spec: 複雑なバッファ変換を全廃し、起動音と同じシンプルなモノラルルートで再生する最終確定版
// =========================================================================

#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <driver/i2s.h>

// -------------------------------------------------------------------------
// BLE通信のUUIDおよびパラメータ設定
// -------------------------------------------------------------------------
#define SERVICE_UUID            "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_EYE_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define CHARACTERISTIC_VOICE_UUID "d0d34192-3eb6-41fb-a15c-0e24177c34dd"
#define CHARACTERISTIC_SERVO_UUID "e0a64192-3eb6-41fb-a15c-0e24177c34dd"
// BLE標準のバッテリーUUID（16ビットUUIDを128ビット形式に拡張したもの）
#define BATTERY_SERVICE_UUID        "0000180f-0000-1000-8000-00805f9b34fb"
#define BATTERY_CHARACTERISTIC_UUID "00002a19-0000-1000-8000-00805f9b34fb"

BLEServer* pServer = nullptr;
BLECharacteristic* pEyeCharacteristic = nullptr;
BLECharacteristic* pVoiceCharacteristic = nullptr;
BLECharacteristic* pServoCharacteristic = nullptr;
BLECharacteristic *pBatteryCharacteristic;
unsigned long lastBatteryUpdateTime = 0;

bool deviceConnected = false;
bool oldDeviceConnected = false;

// -------------------------------------------------------------------------
// LovyanGFX 液晶初期化設定 (GC9A01専用カスタムクラス)
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
    cfg.pin_sclk = 7;          // GPIO 7（シルクはD8） 
    cfg.pin_mosi = 9;        // GPIO 9（シルクはD10）   
    cfg.pin_miso = -1;
    cfg.pin_dc   = 8;          // GPIO 8（シルクはD9） 
    _bus_instance.config(cfg);
    _panel_instance.setBus(&_bus_instance);

    auto p_cfg = _panel_instance.config();
    p_cfg.pin_cs           = 44;  // GPIO 44（シルクはD7） 
    p_cfg.pin_rst          = 43;  // GPIO 43（シルクはD6） 
    p_cfg.panel_width  = 240;
    p_cfg.panel_height  = 240;
    p_cfg.offset_x         = 0;
    p_cfg.offset_y         = 0;
    p_cfg.invert              = true;
    p_cfg.rgb_order       = false;
    _panel_instance.config(p_cfg);
    setPanel(&_panel_instance);
  }
};

LGFX_iRobapp lcd;
LGFX_Sprite canvas(&lcd);

// -------------------------------------------------------------------------
// ピン定義 & グローバル変数
// -------------------------------------------------------------------------
const int PIN_SERVO_PAN  = 1;   // GPIO 1（シルクはD0）
const int PIN_SERVO_TAIL = 2;   // GPIO 2（シルクはD1）

const int PIN_I2S_LRCLK  = 3;   // GPIO 3（シルクはD2） WS
const int PIN_I2S_BCLK   = 4;   // GPIO 4（シルクはD3） BCK
const int PIN_I2S_DIN    = 5;   // GPIO 5（シルクはD4） DATA
const int PIN_LCD_BL     = 6;   // GPIO 6（シルクはD5） Backlight

// 🎯 iPhone側と完全に一致させる16000Hzに目盛りをカチッと固定
#define SAMPLE_RATE      16000 //8000:固定電話 16000:標準 22050:ラジオ 24000:テレビ

Servo servoPan;
Servo servoTail;

float eyeY = 120.0;
float targetEyeY = 120.0;
float eyeX = 120.0;
const float eyeRadius = 45.0;
const float whiteRadius = 95.0;

unsigned long lastBlinkTime = 0;
unsigned long blinkInterval = 3000;
bool isBlinking = false;
float blinkProgress = 0.0;
bool isSleepMode = false;
unsigned long lastInteractionTime = 0;
const unsigned long SLEEP_TIMEOUT = 30000;

volatile bool isAudioPlaying = false;
volatile unsigned long lastAudioPacketTime = 0;
unsigned long tailMotionStartTime = 0;
bool isTailWaggingForVoice = false;

unsigned long batteryStartTime = 0;
uint8_t lastSentLevel = 100;

// -------------------------------------------------------------------------
// I2S オーディオ初期化
// -------------------------------------------------------------------------
void initI2SAudio() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT, 
    //.channel_format = I2S_CHANNEL_FMT_ALL_LEFT,     
    .communication_format = (i2s_comm_format_t)(I2S_COMM_FORMAT_STAND_I2S),
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64, 
    .use_apll = false,
    .tx_desc_auto_clear = true
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = PIN_I2S_BCLK,
    .ws_io_num = PIN_I2S_LRCLK,
    .data_out_num = PIN_I2S_DIN,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  i2s_zero_dma_buffer(I2S_NUM_0);
  Serial.println("[OK] I2S Audio Driver Initialized (Mono Mode).");
}

// -------------------------------------------------------------------------
// 起動時の音再生
// -------------------------------------------------------------------------
void playSystemBootSound() {
  i2s_start(I2S_NUM_0);
  const int note_length = 2000; 
  int16_t sound_buffer[note_length];
  size_t bytes_written;

  // 1音目：ピピッの「ピ」（高いレの音：1174Hz）
  for (int i = 0; i < note_length; i++) {
    float angle = (2.0 * PI * 1174.0 * i) / SAMPLE_RATE;
    sound_buffer[i] = (int16_t)(sin(angle) * 10000); 
  }
  i2s_write(I2S_NUM_0, (const char*)sound_buffer, note_length * sizeof(int16_t), &bytes_written, portMAX_DELAY);
  delay(50); 

  // 2音目：ピピッの「ッピ」（さらに高いラの音：1760Hz）
  for (int i = 0; i < note_length; i++) {
    float angle = (2.0 * PI * 1760.0 * i) / SAMPLE_RATE;
    sound_buffer[i] = (int16_t)(sin(angle) * 10000); 
  }
  i2s_write(I2S_NUM_0, (const char*)sound_buffer, note_length * sizeof(int16_t), &bytes_written, portMAX_DELAY);
  i2s_zero_dma_buffer(I2S_NUM_0); 
}
// -------------------------------------------------------------------------
// BLEサーバー接続状態コールバック
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

// -------------------------------------------------------------------------
// 目の制御データ受信コールバック（左右・上下の2軸データ対応版）
// -------------------------------------------------------------------------
class EyeCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String value = pCharacteristic->getValue();
        if (value.length() > 0) {
            lastInteractionTime = millis();
            isSleepMode = false;

            // iPhoneから「X,Y」（例：「70,150」）というコンマ区切りの文字が届くので分解します
            int commaIndex = value.indexOf(',');
            if (commaIndex != -1) {
                String xStr = value.substring(0, commaIndex);
                String yStr = value.substring(commaIndex + 1);
                
                // ターゲット座標を上下左右、同時に更新！
                eyeX = xStr.toFloat(); 
                targetEyeY = yStr.toFloat();
            } else {
                // コンマがない従来の単発数値は、今まで通り上下（Y軸）の指示として処理
                targetEyeY = value.toFloat();
            }
        }
    }
};

// -------------------------------------------------------------------------
// 音声ストリーミングデータ受信コールバック（ピュア直撃版）
// -------------------------------------------------------------------------
class VoiceCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        // iPhoneから送られてきた生のバイナリデータと正確な長さをそのまま取得
        uint8_t* rawData = pCharacteristic->getData();
        size_t dataLength = pCharacteristic->getLength();

        const int16_t* audioSamples = (const int16_t*)rawData;
        
        if (dataLength > 0 && rawData != nullptr) {
            lastInteractionTime = millis();
            isSleepMode = false;
            lastAudioPacketTime = millis();

            // 話が始まった瞬間だけアンプを起動
            if (!isAudioPlaying) {
                i2s_start(I2S_NUM_0);
                isAudioPlaying = true;
            }

            // データの長さ（180バイト未満の端数パケットなど）を一切気にせず、
            // 届いたバイナリをそのまま遅延ゼロ（非ブロック）でI2Sへ直撃書き込みします！
            size_t bytes_written;
            i2s_write(I2S_NUM_0, (const char*)audioSamples, dataLength, &bytes_written, portMAX_DELAY);

            if (!isTailWaggingForVoice) {
                isTailWaggingForVoice = true;
                tailMotionStartTime = millis();
            }
        }
    }
};

// -------------------------------------------------------------------------
// サーボ動作受信コールバック（ピュア直撃版）
// -------------------------------------------------------------------------
class ServoCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        // アプリから届いたデータを取得
        String command = pCharacteristic->getValue();

        if (command.length() > 0) {
            // String型に変換し、末尾の改行コード（\n）や空白を綺麗に除去
            String command = pCharacteristic->getValue();
            command.trim(); 

            Serial.print("📡 受信したサーボコマンド: ");
            Serial.println(command);

            // 1. 「左を見る」コマンド
            if (command == "look_left") {
                servoPan.write(45); // 例：左向き45度（角度はロボットに合わせて調整してください）
                Serial.println("👀 左を向きます");
            }
            // 2. 「正面をみる」コマンド
            else if (command == "look_front") {
                servoPan.write(90); // 例：正面90度
                Serial.println("👀 正面を向きます");
            }
            // 3. 「右を見る」コマンド
            else if (command == "look_right") {
                servoPan.write(135); // 例：右向き135度
                Serial.println("👀 右を向きます");
            }
            // 4. 「尻尾を振る」コマンド
            else if (command == "wag_tail") {
                Serial.println("🐕 尻尾を振ります！");
                // 尻尾を3回左右にフリフリする即席ループ
                for(int i = 0; i < 3; i++) {
                    servoTail.write(60);  // left
                    delay(200);
                    servoTail.write(120); // right
                    delay(200);
                }
                servoTail.write(90); // 最後に正面（定位置）に戻す
            }
        }
    }
};

// -------------------------------------------------------------------------
// 目の物理演算ロジック
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

// -------------------------------------------------------------------------
// 目の液晶描画処理（上下左右キョロキョロ完全アジャスト版）
// -------------------------------------------------------------------------
void drawEye() {
  canvas.clear(TFT_BLACK); // 背景を黒でリセット

  int leftEyeX = 60;   
  int rightEyeX = 180; 
  int baseEyeY = 120;  // 縦の中心は120

  int customWhiteRadius = 38; 
  int customEyeRadius = 18;   

  // 横（X）だけでなく、縦（Y）の動きにも0.4倍の可愛いブレーキをかける！
  // これにより、iPhoneからの「上下」の指示でも黒目が白目からはみ出さなくなります
  float offsetX = (eyeX - 120.0f) * 0.4f;
  float offsetY = (eyeY - 120.0f) * 0.4f; // 🎯画面中心(120)からのズレを0.4倍に減衰

  // 1. 【左目】白目と、補正された上下左右の黒目
  canvas.fillCircle(leftEyeX, baseEyeY, customWhiteRadius, TFT_WHITE); 
  canvas.fillCircle(leftEyeX + offsetX, baseEyeY + offsetY, customEyeRadius, TFT_BLACK); // 🎯縦方向(baseEyeY + offsetY)に修正
  canvas.fillCircle(leftEyeX + offsetX - 4, baseEyeY + offsetY - 4, 3, TFT_WHITE);       // ハイライトも追従

  // 2. 【右目】白目と、補正された上下左右の黒目
  canvas.fillCircle(rightEyeX, baseEyeY, customWhiteRadius, TFT_WHITE); 
  canvas.fillCircle(rightEyeX + offsetX, baseEyeY + offsetY, customEyeRadius, TFT_BLACK); // 🎯縦方向(baseEyeY + offsetY)に修正
  canvas.fillCircle(rightEyeX + offsetX - 4, baseEyeY + offsetY - 4, 3, TFT_WHITE);       // ハイライトも追従

  // 3. 【まぶた】瞬きのアニメーション（変更なし）
  float currentProgress = (blinkProgress > 1.0f) ? (2.0f - blinkProgress) : blinkProgress;
  if (currentProgress > 0.0f) {
    int lidHeight = (int)(120 * currentProgress);
    canvas.fillRect(0, 0, 240, lidHeight, TFT_BLACK);          
    canvas.fillRect(0, 240 - lidHeight, 240, lidHeight, TFT_BLACK); 
  }

  canvas.pushSprite(0, 0); 
}
// -------------------------------------------------------------------------
// USB（5V）が接続されているか（＝充電中か）を判定する関数
// -------------------------------------------------------------------------
extern "C" {
bool usb_serial_jtag_is_connected(void);
}
bool isUsbConnected() {
    // 1. チップの内蔵回路がUSBを検知しているか
    if (usb_serial_jtag_is_connected()) {
        return true;
    }
    
    // 2. Arduinoの標準USBシリアルオブジェクトがアクティブか（PC接続時用）
    if (Serial) { 
        return true; 
    }
    
    return false;
}

// -------------------------------------------------------------------------
// 実際の電圧（アナログ値）を読み取ってパーセント（0-100）に変換する関数
// -------------------------------------------------------------------------
uint8_t getBatteryPercentage() {

    // 💡 1. USBが繋がっている（充電中）なら、強制的に100%にする
    if (isUsbConnected()) {
        return 100; 
    }

    // ⚠️ お使いのロボット基板の回路に合わせてピン番号（例: GPIO 1）を変更してください
    int analogValue = analogRead(1); 
    
    // 電圧リポバッテリーの場合の簡易計算例（3.3V〜4.2V付近を0-100%にマッピング）
    // ※お使いの基板（M5Stackやオリジナル回路）の分圧比に合わせて調整が必要です
    float voltage = (analogValue * 3.3 / 4095.0) * 2.0; // 2倍分圧回路の場合
    
    int percentage = (int)((voltage - 3.3) / (4.2 - 3.3) * 100.0);
    if (percentage > 100) percentage = 100;
    if (percentage < 0) percentage = 0;
    
    return (uint8_t)percentage;
}

// -------------------------------------------------------------------------
// 起動セットアップ
// -------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0));

  // 液晶とバックライトの起動
  lcd.init();
  pinMode(PIN_LCD_BL, OUTPUT);
  digitalWrite(PIN_LCD_BL, HIGH);
  canvas.createSprite(240, 240);
  
  // サーボタイマー割り当て
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  servoPan.setPeriodHertz(50);
  servoTail.setPeriodHertz(50);
  servoPan.attach(PIN_SERVO_PAN, 500, 2400);
  servoTail.attach(PIN_SERVO_TAIL, 500, 2400);
  servoPan.write(90);
  servoTail.write(90);
  
  // I2Sオーディオの起動
  initI2SAudio();
  Serial.println("🔊 システム起動音を再生します...");
  playSystemBootSound();

  // 🔇起動音が終わったら一度バッファをクリアして、アンプを止めて待機（無音化）
  i2s_zero_dma_buffer(I2S_NUM_0); 
  i2s_stop(I2S_NUM_0);            
  Serial.println(">>> 雑音を完全シャットアウトしました。スピーカーは安全に静止しています。");

  Serial.println("🤖 起動セルフチェック開始：首と尻尾を動かします");

  // 1. 首を「右 ➔ 正面 ➔ 左 ➔ 正面」にシャキシャキ動かす
  servoPan.write(60);   delay(300);  // 右を向く
  servoPan.write(90);   delay(200);  // 正面に戻る
  servoPan.write(120);  delay(300);  // 左を向く
  servoPan.write(90);   delay(300);  // 正面に戻って静止

  // 2. 尻尾をお尻フリフリと「2回」振る
  for(int i = 0; i < 2; i++) {
    servoTail.write(120); delay(150);
    servoTail.write(60);  delay(150);
  }
  servoTail.write(90);  delay(100);
  
  Serial.println("🚀 オープニング演出完了！自律モードに移行します。");

  // WiFiを起動　WiFiのMACアドレスから下4桁を取得して固有デバイス名を生成
  WiFi.mode(WIFI_MODE_STA);
  // 無線チップが完全に目を覚ますまで、100ミリ秒（0.1秒）だけ待ちます
  delay(100); 
  // 準備が整ったので、安全に本物のMacアドレスを取得！
  String macStr = WiFi.macAddress();
  macStr.replace(":", "");
  // 下4桁を切り出してデバイス名にくっつける
  String macSuffix = macStr.substring(macStr.length() - 4);
  String deviceName = "iRobapp-mini-" + macSuffix;
  Serial.printf(">>> デバイス名を確定しました: %s\n", deviceName.c_str());

  BLEDevice::init(deviceName.c_str()); 
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  BLEService *pBatteryService = pServer->createService(BATTERY_SERVICE_UUID);

  pEyeCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_EYE_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  pEyeCharacteristic->setCallbacks(new EyeCallbacks());

  pVoiceCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_VOICE_UUID,
    BLECharacteristic::PROPERTY_WRITE    |
    BLECharacteristic::PROPERTY_WRITE_NR | 
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pVoiceCharacteristic->setCallbacks(new VoiceCallbacks());

  pServoCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_SERVO_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  pServoCharacteristic->setCallbacks(new ServoCallbacks());

  pVoiceCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  // バッテリー残量特性（読み取り & 通知可能）の作成
  pBatteryCharacteristic = pBatteryService->createCharacteristic(
    BATTERY_CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  // デフォルト値をセット
  uint8_t initialLevel = getBatteryPercentage();
  pBatteryCharacteristic->setValue(&initialLevel, 1);

  // サービスを開始
  pBatteryService->start();


  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->addServiceUUID(BATTERY_SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  
  Serial.println(">>> BLEアドバタイズ中...");
  lastBlinkTime = millis();
  lastInteractionTime = millis();
}

// -------------------------------------------------------------------------
// メインループ
// -------------------------------------------------------------------------
void loop() {
    // 4. 30秒ごとにバッテリー残量を更新してiPhoneに通知する
    if (millis() - lastBatteryUpdateTime > 30000) {
        lastBatteryUpdateTime = millis();
        
        uint8_t currentLevel = getBatteryPercentage();
        pBatteryCharacteristic->setValue(&currentLevel, 1);
        pBatteryCharacteristic->notify(); // iPhoneへ通知を送る
        
        Serial.printf("🔋 バッテリー残量を通知しました: %d%%\n", currentLevel);
    }

  if (!deviceConnected && oldDeviceConnected) {
      delay(500);
      pServer->startAdvertising();
      oldDeviceConnected = deviceConnected;
  }
  if (deviceConnected && !oldDeviceConnected) {
      oldDeviceConnected = deviceConnected;
  }

  // 🔊 音声の無通信タイムアウト判定（パケットが300ms途絶えたらアンプを安全に寝かせる）
  if (isAudioPlaying && (millis() - lastAudioPacketTime > 300)) {
    i2s_zero_dma_buffer(I2S_NUM_0);
    i2s_stop(I2S_NUM_0);
    isAudioPlaying = false;
    Serial.println(">>> 音声ストリーム終了。アンプを省電力停止しました。");
  }

  if (millis() - lastInteractionTime > SLEEP_TIMEOUT) {
    isSleepMode = true;
  }

  // おしゃべり受信時の尻尾フリフリ制御
  if (isTailWaggingForVoice) {
    unsigned long elapsed = millis() - tailMotionStartTime;
    if (elapsed < 135) {
      servoTail.write(120);
    } else if (elapsed < 270) {
      servoTail.write(60);
    } else if (elapsed < 405) {
      servoTail.write(120);
    } else if (elapsed < 540) {
      servoTail.write(60);
    } else {
      servoTail.write(90);
      isTailWaggingForVoice = false; 
    }
  } 
  else if (!isSleepMode && random(0, 1000) < 3) {
    servoPan.write(random(60, 120));
    if(random(0, 2) == 0) {
      servoTail.write(110); 
      delay(80);
      servoTail.write(70);  
      delay(80);
      servoTail.write(90);
    }
  }

  updateEyePhysics();
  drawEye();
  delay(16);
}
