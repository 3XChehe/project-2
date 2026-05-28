#include <stdio.h>
#include <winsock2.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#pragma comment(lib, "ws2_32.lib")

#define PORT 8888
#define MAX_CLIENTS 64

int main()
{
    WSADATA wsa;
    SOCKET server_sock;
    struct sockaddr_in server;
    char buffer[1024];
    unsigned long ul = 1;

    // Khởi tạo Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0)
    {
        printf("Failed. Error Code : %d", WSAGetLastError());
        return 1;
    }

    // Tạo Socket
    server_sock = socket(AF_INET, SOCK_STREAM, 0);
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons(PORT);

    // Chế độ Non-blocking cho Server
    ioctlsocket(server_sock, FIONBIO, &ul);

    if (bind(server_sock, (struct sockaddr *)&server, sizeof(server)) == SOCKET_ERROR)
    {
        printf("Bind failed with error code : %d", WSAGetLastError());
        return 1;
    }

    listen(server_sock, 5);
    printf("Server dang lang nghe tai Port %d...\n", PORT);
    printf("Dinh dang ghi file: R: [Raw] F: [Filtered] T: [Timestamp]\n");

    SOCKET clients[MAX_CLIENTS];
    int nclients = 0;

    // Mở file log (a = append)
    FILE *f = fopen("output.txt", "a");
    if (f == NULL)
    {
        printf("Khong the mo file output.txt\n");
        return 1;
    }

    while (1)
    {
        // Chấp nhận kết nối mới
        SOCKET client = accept(server_sock, NULL, NULL);
        if (client != INVALID_SOCKET)
        {
            if (nclients < MAX_CLIENTS)
            {
                printf("New Client Connected: %d\n", client);
                ioctlsocket(client, FIONBIO, &ul); // Set non-blocking cho client
                clients[nclients++] = client;
            }
            else
            {
                closesocket(client);
            }
        }

        // Kiểm tra dữ liệu từ các client
        for (int i = 0; i < nclients; i++)
        {
            int len = recv(clients[i], buffer, sizeof(buffer) - 1, 0);

            if (len > 0)
            {
                buffer[len] = '\0';

                // Xử lý dữ liệu nhận được (có thể chứa nhiều dòng \n)
                char *line = strtok(buffer, "\n");
                while (line != NULL)
                {
                    char mac[32];
                    float raw_rssi, filtered_rssi;

                    // Định dạng ESP32 gửi: "MAC,RAW,FILTERED"
                    if (sscanf(line, "%[^,],%f,%f", mac, &raw_rssi, &filtered_rssi) == 3)
                    {
                        time_t now = time(NULL);

                        // Ghi vào file theo định dạng yêu cầu
                        fprintf(f, "MAC: %s R: %.2f F: %.2f T: %ld\n", mac, raw_rssi, filtered_rssi, now);
                        fflush(f); // Ép ghi dữ liệu vào ổ đĩa ngay

                        // In ra màn hình để theo dõi
                        printf("[%s] Raw: %.2f | Filtered: %.2f | Time: %ld\n",
                               mac, raw_rssi, filtered_rssi, now);
                    }
                    line = strtok(NULL, "\n");
                }
            }
            else if (len == 0)
            {
                printf("Client %d disconnected\n", clients[i]);
                closesocket(clients[i]);
                clients[i] = clients[nclients - 1];
                nclients--;
                i--;
            }
        }
        Sleep(10); // Tránh chiếm dụng 100% CPU
    }

    fclose(f);
    WSACleanup();
    return 0;
}