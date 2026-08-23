// =========================================================================
// File: firmware/main/main.ino
// Description: iRobapp-mini メイン制御ファームウェア
// Spec: LovyanGFXによるリアルタイム瞳演算、乱生まばたき、BLEコマンド待機
// GPIO Mapping: D1=GPIO2(RES), D2=GPIO3(DC), D3=GPIO4(CS), D8=GPIO8(SDA), D10=GPIO10(SCL)
//               D4=GPIO5(Pan Servo), D5=GPIO6(Tail Servo)
// =========================================================================

#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <ESP32Servo.h>

// -------------------------------------------------------------------------
// 1. LovyanGFX 液晶初期化設定 (GC9A01専用カスタムクラス)
// -------------------------------------------------------------------------
class LGFX_iRobapp : public lgfx::LGFX_Device {
  lgfx::Panel_GC9A01 _panel_instance;
  lgfx::Bus_SPI      _bus_instance;

public:
  LGFX_iRobapp() {
    // SPIバスの設定
    auto cfg = _bus_instance.config();
    cfg.spi_host = SPI2_HOST;     // ESP32-S3の標準SPI
    cfg.spi_mode = 0;
    cfg.freq_write = 40000000;    // 画面のチラつきを防ぐ40MHz爆速転送
    cfg.pin_sclk = 10;            // シルク D10 -> GPIO 10 (SCL)
    cfg.pin_mosi = 8;             // シルク D8  -> GPIO 8  (SDA)
    cfg.pin_miso = -1;
    cfg.pin_dc   = 3;             // シルク D2  -> GPIO 3  (DC)
    _bus_instance.config(cfg);
    _panel_instance.setBus(&_bus_instance);

    // パネルの設定
    auto p_cfg = _panel_instance.config();
    p_cfg.pin_cs           = 4;   // シルク D3  -> GPIO 4  (CS)
    p_cfg.pin_rst          = 2;   // シルク D1  -> GPIO 2  (RES)
    p_cfg.panel_width      = 240; // GC9A01 標準解像度
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
LGFX_Sprite canvas(&lcd); // 描画のチラつきを100%防ぐためのダブルバッファ用スプライト

// -------------------------------------------------------------------------
// 2. ピン定義 & グローバル変数
// -------------------------------------------------------------------------
const int PIN_SERVO_PAN  = 5;   // シルク D4 -> GPIO 5
const int PIN_SERVO_TAIL = 6;   // シルク D5 -> GPIO 6

Servo servoPan;
Servo servoTail;

// 瞳のアニメーション用変数
float eyeY = 120.0;             // 黒目の現在のY座標 (中心は120)
float targetEyeY = 120.0;       // 黒目の目標Y座標 (iPhoneから指示される値)
const float eyeX = 120.0;       // 黒目のX座標 (正面固定)
const float eyeRadius = 45.0;   // 黒目の半径
const float whiteRadius = 95.0; // 白目の半径

// まばたき・スリープ状態管理
unsigned long lastBlinkTime = 0;
unsigned long blinkInterval = 3000; // 次のまばたきまでの時間 (乱数で変動)
bool isBlinking = false;
float blinkProgress = 0.0;      // 0.0 = 完全開眼, 1.0 = 完全閉眼
bool isSleepMode = false;
unsigned long lastInteractionTime = 0;
const unsigned long SLEEP_TIMEOUT = 30000; // 30秒操作がないとスリープ

// -------------------------------------------------------------------------
// 3. クアドラティック・イージング関数 (滑らかな視線移動用)
// -------------------------------------------------------------------------
void updateEyePhysics() {
  if (isSleepMode) {
    // スリープ時はまぶたを閉じる方向へ進める
    if (blinkProgress < 1.0f) blinkProgress += 0.1f;
    return;
  }

  // 視線のヌルヌル追従計算 (イージングによる目標値への接近)
  eyeY += (targetEyeY - eyeY) * 0.15f; 

  // まばたきアニメーションの進行管理
  if (!isBlinking) {
    if (millis() - lastBlinkTime > blinkInterval) {
      isBlinking = true;
      blinkProgress = 0.0f;
    }
  } else {
    blinkProgress += 0.25f; // まばたきの速度
    if (blinkProgress >= 2.0f) { // 往復完了
      isBlinking = false;
      lastBlinkTime = millis();
      // 3パターンの間隔を乱数で決定 (要件定義通り)
      int pattern = random(0, 3);
      if (pattern == 0) blinkInterval = 2000;
      else if (pattern == 1) blinkInterval = 4000;
      else blinkInterval = 6000;
    }
  }
}

// ---------------------------------------------------------
// 4. LovyanGFXによるリアルタイム瞳描画ロジック
// ---------------------------------------------------------
void drawEye() {
  canvas.clear(TFT_BLACK);

  // ① 白目の描画
  canvas.fillCircle(120, 120, whiteRadius, TFT_WHITE);

  // ② 黒目（瞳）の描画
  if (blinkProgress < 1.0f) {
    // まぶたに隠れない範囲で黒目の位置を動かす
    float currentY = eyeY;
    canvas.fillCircle(eyeX, currentY, eyeRadius, TFT_BLACK);
    // キラキラ（ハイライト）を入れて生命感を演出
    canvas.fillCircle(eyeX - 12, currentY - 12, 10, TFT_WHITE);
  }

  // ③ 【核心】まぶたの描画（上下から閉じるリアルなまばたき演算）
  float currentProgress = (blinkProgress > 1.0f) ? (2.0f - blinkProgress) : blinkProgress;
  if (currentProgress > 0.0f) {
    int lidHeight = (int)(120 * currentProgress);
    // 上まぶた
    canvas.fillRect(0, 0, 240, lidHeight, TFT_BLACK);
    // 下まぶた
    canvas.fillRect(0, 240 - lidHeight, 240, lidHeight, TFT_BLACK);
  }

  // ダブルバッファの内容を一気に液晶へ転送（チラつき完全ゼロ）
  canvas.pushSprite(0, 0);
}

// ---------------------------------------------------------
// 5. Arduino 起動セットアップ
// ---------------------------------------------------------
void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0)); // 乱数の初期化

  // 液晶の初期化とスプライト（メモリ）の確保
  lcd.init();
  canvas.createSprite(240, 240);
  
  // サーボモーターの初期設定
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  servoPan.setPeriodHertz(50);
  servoTail.setPeriodHertz(50);
  servoPan.attach(PIN_SERVO_PAN, 500, 2400);
  servoTail.attach(PIN_SERVO_TAIL, 500, 2400);

  // 初期位置の指定
  servoPan.write(90);
  servoTail.write(90);
  
  lastBlinkTime = millis();
  lastInteractionTime = millis();
}

// ---------------------------------------------------------
// 6. メインループ (描画・物理演算・自律動作の統合)
// ---------------------------------------------------------
void loop() {
  // ① シリアル通信またはBLEコマンドのモック待機 (のちにBLEと置換)
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    lastInteractionTime = millis();
    isSleepMode = false;

    if (cmd.startsWith("EYE:")) {
      // 将来の視線連動を見据え、数値を直接受け取れる構造にする
      // 3パターンの判定用（iPhone側から 60=上, 120=中, 180=下 のように送る想定）
      targetEyeY = cmd.substring(4).toFloat();
    } 
    else if (cmd == "TALK") {
      // トリガー動作：尻尾を2回キュキュッと振る (要件定義通り)
      for(int i=0; i<2; i++) {
        servoTail.write(120); delay(150);
        servoTail.write(60);  delay(150);
      }
      servoTail.write(90);
    }
  }

  // ② 自律動作：スリープチェック
  if (millis() - lastInteractionTime > SLEEP_TIMEOUT) {
    isSleepMode = true;
  }

  // ③ 自律動作：乱数ベースの不定期な首振りと尻尾振りの演出 (要件定義通り)
  if (!isSleepMode && random(0, 1000) < 3) { // 約10秒に数回の確率
    servoPan.write(random(60, 120));          // 首をきょろきょろ
    if(random(0, 2) == 0) {
      servoTail.write(110); delay(100);       // 尻尾をフリフリ
      servoTail.write(70);  delay(100);
      servoTail.write(90);
    }
  }

  // ④ 物理演算の更新 ＆ 画面のリフレッシュ
  updateEyePhysics();
  drawEye();

  delay(16); // 秒間約60フレームの超滑らかな更新テンポを維持
}
