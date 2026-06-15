#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

const char *ssid = "CAO SY";
const char *password = "0936074767";
const char *serverIP = "192.168.100.16";
const int serverPort = 8888;
WiFiClient client;

// ===== CẤU TRÚC KALMAN =====
typedef struct {
    float q; // Nhiễu hệ thống (Process noise covariance)
    float r; // Nhiễu đo lường (Measurement noise covariance)
    float x; // Giá trị ước lượng (Estimated value)
    float p; // Sai số ước lượng (Estimation error covariance)
    float k; // Hệ số Kalman Gain
    bool is_initialized;
} KalmanFilter;

// Khởi tạo bộ lọc với tham số tối ưu cho Real-time Tracking (Phản ứng nhanh)
void kalman_init(KalmanFilter *f, float q, float r, float initial_value) {
    f->q = q;
    f->r = r;
    f->x = initial_value;
    f->p = 1.0;
    f->is_initialized = true;
}

float kalman_update(KalmanFilter *f, float measurement) {
    if (!f->is_initialized) {
        // Nếu bộ lọc chưa từng chạy, lấy luôn giá trị đo đầu tiên làm gốc để tránh trễ
        kalman_init(f, 0.1f, 4.0f, measurement);
        return measurement;
    }
    f->p = f->p + f->q;
    f->k = f->p / (f->p + f->r);
    f->x = f->x + f->k * (measurement - f->x);
    f->p = (1.0 - f->k) * f->p;
    return f->x;
}

// Bộ lọc Kalman riêng cho Beacon mục tiêu
KalmanFilter targetBeaconFilter = {0, 0, 0, 0, 0, false}; 

// ===== BLE CALLBACK =====
class MyCallbacks : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        // Lọc đúng UUID mục tiêu của bạn
        if (advertisedDevice.isAdvertisingService(BLEUUID("12345678-1234-1234-1234-1234567890ab"))) {
            
            float rawRSSI = (float)advertisedDevice.getRSSI();
            
            // Cập nhật vào bộ lọc riêng của Beacon này
            float filteredRSSI = kalman_update(&targetBeaconFilter, rawRSSI);

            String myMAC = WiFi.macAddress();
            myMAC.toLowerCase(); 

            if (client.connected()) {
                // Gửi dữ liệu lên Server C
                client.printf("%s,%.2f,%.2f\n", myMAC.c_str(), rawRSSI, filteredRSSI);
                Serial.printf("[%s] Raw: %.1f | Kalman: %.1f\n", myMAC.c_str(), rawRSSI, filteredRSSI);
            }
        }
    }
};

void setup() {
    Serial.begin(115200);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected OK!");

    BLEDevice::init("");
    BLEScan *pScan = BLEDevice::getScan();
    pScan->setAdvertisedDeviceCallbacks(new MyCallbacks(), true);
    pScan->setActiveScan(true);
}

void loop() {
    if (!client.connected()) {
        if (client.connect(serverIP, serverPort)) {
            Serial.println("Đã kết nối thành công tới Server C!");
        }
        delay(1000);
    }

    BLEScan *pScan = BLEDevice::getScan();
    // Quét chu kỳ ngắn 0.3 giây giúp cập nhật vị trí thời gian thực cực nhạy
    pScan->start(0.3, false); 
    pScan->clearResults(); 
}