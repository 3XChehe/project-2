#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

const char *ssid = "CAO SY";
const char *password = "0936074767";
const char *serverIP = "192.168.100.8";
const int serverPort = 8888;
WiFiClient client;

// ===== CẤU TRÚC KALMAN =====
typedef struct
{
    float q;
    float r;
    float x;
    float p;
    float k;
} KalmanFilter;

KalmanFilter rssiFilter;

void kalman_init(KalmanFilter *f, float q, float r, float initial_value)
{
    f->q = q;
    f->r = r;
    f->x = initial_value;
    f->p = 1.0;
}

float kalman_update(KalmanFilter *f, float measurement)
{
    f->p = f->p + f->q;
    f->k = f->p / (f->p + f->r);
    f->x = f->x + f->k * (measurement - f->x);
    f->p = (1.0 - f->k) * f->p;
    return f->x;
}

// ===== BLE CALLBACK =====
class MyCallbacks : public BLEAdvertisedDeviceCallbacks
{
    void onResult(BLEAdvertisedDevice advertisedDevice)
    {
        // Lọc đúng UUID Beacon bạn đang dùng
        if (advertisedDevice.isAdvertisingService(BLEUUID("12345678-1234-1234-1234-1234567890ab")))
        {

            float rawRSSI = (float)advertisedDevice.getRSSI();
            float filteredRSSI = kalman_update(&rssiFilter, rawRSSI);

            // Lấy MAC của chính con ESP32 này (Scanner MAC)
            String myMAC = WiFi.macAddress();
            myMAC.toLowerCase(); // Server C thường so sánh chuỗi viết thường

            if (client.connected())
            {
                // ĐỊNH DẠNG KHỚP VỚI sscanf(line, "%[^,],%f,%f"):
                // ScannerMAC,RawRSSI,FilteredRSSI
                client.printf("%s,%.2f,%.2f\n",
                              myMAC.c_str(),
                              rawRSSI,
                              filteredRSSI);

                Serial.printf("Gửi tới Server C: %s, RSSI: %.2f\n", myMAC.c_str(), filteredRSSI);
            }
        }
    }
};

void setup()
{
    Serial.begin(115200);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi OK!");

    // Khởi tạo Kalman
    kalman_init(&rssiFilter, 0.05, 20.0, -60);

    BLEDevice::init("");
    BLEScan *pScan = BLEDevice::getScan();
    pScan->setAdvertisedDeviceCallbacks(new MyCallbacks(), true);
    pScan->setActiveScan(true);
}

void loop()
{
    if (!client.connected())
    {
        if (client.connect(serverIP, serverPort))
        {
            Serial.println("Đã kết nối Server C!");
        }
        delay(1000);
    }

    BLEScan *pScan = BLEDevice::getScan();
    pScan->start(0.5, false);
    pScan->clearResults();
}