#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEAdvertising.h>

#define SERVICE_UUID "12345678-1234-1234-1234-1234567890ab"

void setup() {
  Serial.begin(115200);
  BLEDevice::init("ESP32_BEACON");
  
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  
  // 200ms = 320 * 0.625ms
  pAdvertising->setMinInterval(0x0140); 
  pAdvertising->setMaxInterval(0x0140); 
  
  BLEDevice::startAdvertising();
  Serial.println("Beacon dang phat moi 200ms...");
}

void loop() {
  delay(1000);
}