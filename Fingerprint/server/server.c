#include <stdio.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <string.h>

#pragma comment(lib, "ws2_32.lib")

#define PORT 8888
#define PYTHON_PORT 9999
#define MAX_CLIENTS 10

typedef struct
{
    char mac[32];
    float last_filtered_rssi;
    int updated;
} Scanner;

// Giữ nguyên danh sách MAC của bạn
Scanner scanners[3] = {
    {"c8:f0:9e:26:48:80", -100.0f, 0}, // S1
    {"1c:c3:ab:c3:f7:78", -100.0f, 0}, // S2
    {"b0:cb:d8:9a:64:40", -100.0f, 0}  // S3
};

int main()
{
    WSADATA wsa;
    SOCKET server_sock, udp_sock;
    struct sockaddr_in server_addr, py_addr;
    unsigned long ul = 1;
    char buffer[1024];

    WSAStartup(MAKEWORD(2, 2), &wsa);

    server_sock = socket(AF_INET, SOCK_STREAM, 0);
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);
    bind(server_sock, (struct sockaddr *)&server_addr, sizeof(server_addr));
    listen(server_sock, 5);
    ioctlsocket(server_sock, FIONBIO, &ul);

    udp_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    py_addr.sin_family = AF_INET;
    py_addr.sin_port = htons(PYTHON_PORT);
    inet_pton(AF_INET, "127.0.0.1", &py_addr.sin_addr);

    printf("RSSI Forwarding Server Ready... Sending to Python on Port %d\n", PYTHON_PORT);

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
                                scanners[j].last_filtered_rssi = filtered;
                                scanners[j].updated = 1;
                                break;
                            }
                        }
                    }
                    line = strtok(NULL, "\n");
                }

                // Gửi sang Python khi nhận đủ dữ liệu từ 3 trạm (hoặc có cập nhật mới)
                if (scanners[0].updated && scanners[1].updated && scanners[2].updated)
                {
                    char payload[128];
                    // Gửi RSSI trực tiếp, không tính khoảng cách ở đây
                    sprintf(payload, "%.2f,%.2f,%.2f",
                            scanners[0].last_filtered_rssi,
                            scanners[1].last_filtered_rssi,
                            scanners[2].last_filtered_rssi);

                    sendto(udp_sock, payload, (int)strlen(payload), 0, (struct sockaddr *)&py_addr, sizeof(py_addr));
                    printf("Forwarded RSSI: %s\n", payload);

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