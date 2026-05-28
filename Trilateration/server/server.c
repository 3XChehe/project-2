#include <stdio.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#pragma comment(lib, "ws2_32.lib")

#define PORT 8888
#define PYTHON_PORT 9999
#define MAX_CLIENTS 10

typedef struct
{
    char mac[32];
    float n_val;     // Hệ số n riêng cho từng con
    double distance; // Đơn vị: cm
    int updated;
    float rssi0; // RSSI0 riêng
} Scanner;

Scanner scanners[3] = {
    {"c8:f0:9e:26:48:80", 1.85f, 0.0, 0, -52.54654354}, // Scanner 1
    {"d4:e9:f4:b1:69:a0", 1.6f, 0.0, 0, -61.26078972},  // Scanner 2
    {"b0:cb:d8:9a:64:40", 4.3f, 0.0, 0, -51.24867374}   // Scanner 3
};

// Hàm tính khoảng cách linh hoạt theo n của từng Scanner
double calculate_distance_cm(float rssi, float n, int j)
{
    if (rssi >= 0)
        return 0; // Tránh lỗi log nếu RSSI dương (nhiễu)
    double dist_m = pow(10.0, (double)(scanners[j].rssi0 - rssi) / (10.0 * (double)n));
    return dist_m * 100.0;
}

int main()
{
    WSADATA wsa;
    SOCKET server_sock, udp_sock;
    struct sockaddr_in server_addr, py_addr;
    unsigned long ul = 1;
    char buffer[1024];

    WSAStartup(MAKEWORD(2, 2), &wsa);

    // Setup TCP Server (Nhận từ ESP32)
    server_sock = socket(AF_INET, SOCK_STREAM, 0);
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    bind(server_sock, (struct sockaddr *)&server_addr, sizeof(server_addr));
    listen(server_sock, 5);
    ioctlsocket(server_sock, FIONBIO, &ul);

    // Setup UDP Client (Gửi tới Python)
    udp_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    py_addr.sin_family = AF_INET;
    py_addr.sin_port = htons(PYTHON_PORT);
    inet_pton(AF_INET, "127.0.0.1", &py_addr.sin_addr);

    printf("Server Multi-N Ready. S1(n=1.85), S2(n=1.6), S3(n=4.3)\n");

    SOCKET clients[MAX_CLIENTS] = {0};
    int nclients = 0;

    while (1)
    {
        SOCKET new_client = accept(server_sock, NULL, NULL);
        if (new_client != INVALID_SOCKET)
        {
            ioctlsocket(new_client, FIONBIO, &ul);
            if (nclients < MAX_CLIENTS)
                clients[nclients++] = new_client;
        }

        for (int i = 0; i < nclients; i++)
        {
            int len = recv(clients[i], buffer, sizeof(buffer) - 1, 0);
            if (len > 0)
            {
                buffer[len] = '\0';
                char *line = strtok(buffer, "\n");
                while (line != NULL)
                {
                    char sender_mac[32];
                    float raw, filtered;
                    if (sscanf(line, "%[^,],%f,%f", sender_mac, &raw, &filtered) == 3)
                    {
                        for (int j = 0; j < 3; j++)
                        {
                            if (strcmp(sender_mac, scanners[j].mac) == 0)
                            {
                                scanners[j].distance = calculate_distance_cm(filtered, scanners[j].n_val, j);
                                scanners[j].updated = 1;
                                break;
                            }
                        }
                    }
                    line = strtok(NULL, "\n");
                }

                // gui cho frontend neu co du lieu moi
                // if (scanners[0].updated)
                if (scanners[0].updated && scanners[1].updated && scanners[2].updated)
                {
                    char payload[128];
                    sprintf(payload, "%.2f,%.2f,%.2f",
                            scanners[0].distance, scanners[1].distance, scanners[2].distance);
                    sendto(udp_sock, payload, (int)strlen(payload), 0, (struct sockaddr *)&py_addr, sizeof(py_addr));

                    printf("Dist(cm) -> S1:%.1f | S2:%.1f | S3:%.1f\n",
                           scanners[0].distance, scanners[1].distance, scanners[2].distance);

                    scanners[0].updated = scanners[1].updated = scanners[2].updated = 0;
                }
            }
            else if (len == 0)
            {
                closesocket(clients[i]);
                clients[i] = clients[--nclients];
            }
        }
        Sleep(10);
    }
    return 0;
}