#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// ===== CẤU HÌNH WIFI & SERVER =====
const char* ssid = "CAO SY";
const char* password = "0936074767";
const char* serverIP = "192.168.100.11";
const int serverPort = 8888;
WiFiClient client;

// ===== CẤU TRÚC KALMAN =====
typedef struct {
    float q; // Nhiễu hệ thống
    float r; // Nhiễu đo đạc (Dựa trên phương sai bạn tính)
    float x; // Giá trị ước lượng (RSSI sau lọc)
    float p; // Sai số ước lượng
    float k; // Hệ số Kalman
} KalmanFilter;

KalmanFilter rssiFilter;

void kalman_init(KalmanFilter* f, float q, float r, float initial_value) {
    f->q = q; f->r = r; f->x = initial_value; f->p = 1.0;
}

float kalman_update(KalmanFilter* f, float measurement) {
    f->p = f->p + f->q;
    f->k = f->p / (f->p + f->r);
    f->x = f->x + f->k * (measurement - f->x);
    f->p = (1.0 - f->k) * f->p;
    return f->x;
}

// ===== BLE CALLBACK =====
class MyCallbacks : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        if (advertisedDevice.isAdvertisingService(BLEUUID("12345678-1234-1234-1234-1234567890ab"))) {
            float rawRSSI = (float)advertisedDevice.getRSSI();
            
            // Cập nhật bộ lọc Kalman
            float filteredRSSI = kalman_update(&rssiFilter, rawRSSI);
            
            if (client.connected()) {
                // Gửi cả 2 giá trị để bạn so sánh trên Server
                // Định dạng: MAC,Raw_RSSI,Filtered_RSSI
                client.printf("%s,%.2f,%.2f\n", 
                               advertisedDevice.getAddress().toString().c_str(), 
                               rawRSSI, 
                               filteredRSSI);
            }
            Serial.printf("Raw: %.2f | Kalman: %.2f\n", rawRSSI, filteredRSSI);
        }
    }
};

void setup() {
    Serial.begin(115200);
    
    // Khởi tạo WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
    
    // Khởi tạo Kalman: Q=0.05 (mức độ mượt), R=20.0 (dựa trên phương sai trung bình của bạn)
    kalman_init(&rssiFilter, 0.05, 20.0, -65.0);

    BLEDevice::init("");
    BLEScan* pScan = BLEDevice::getScan();
    pScan->setAdvertisedDeviceCallbacks(new MyCallbacks(), true); // true: nhận tin trùng lặp
    pScan->setActiveScan(false);
}

void loop() {
    if (!client.connected()) {
        client.connect(serverIP, serverPort);
    }
    
    BLEScan* pScan = BLEDevice::getScan();
    pScan->start(0.5, false); // Quét mỗi 0.5s để cập nhật dữ liệu
    pScan->clearResults();
}