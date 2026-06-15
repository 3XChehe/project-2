#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEAdvertising.h>

#define SERVICE_UUID "12345678-1234-1234-1234-1234567890ab"

void setup() {
  Serial.begin(115200);
  BLEDevice::init("ESP32_TAG_REALTIME");
  
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  
  // --- TỐI ƯU CHO REAL-TIME TRACKING ---
  // Đặt chu kỳ phát lý tưởng khoảng 100ms để 3 trạm Scanner bắt sóng kịp thời
  // 100ms = 160 * 0.625ms = 0x00A0
  // 120ms = 192 * 0.625ms = 0x00C0
  pAdvertising->setMinInterval(0x00A0); // Khoảng cách tối thiểu ~100ms
  pAdvertising->setMaxInterval(0x00C0); // Khoảng cách tối đa ~120ms
  
  // Bật tính năng Scan Response để Scanner lấy thông tin nhanh hơn
  pAdvertising->setScanResponse(true);
  
  BLEDevice::startAdvertising();
  Serial.println("Tag di chuyển: Đang phát siêu tốc ~100ms để định vị Real-time...");
}

void loop() {
  // Để nguyên delay(1000) ở đây vì BLE Advertising chạy bằng luồng phần cứng độc lập (Controller),
  // không bị ảnh hưởng bởi hàm delay của CPU chính.
  delay(1000);
}