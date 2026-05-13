#include <stdio.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "crater_can.h"


#define TX_PIN 4
#define RX_PIN 5


// ECHO TASK
// This task echoes back every received message
void can_echo_task(void *pvParameters) {
    can_frame_t rx_frame;
    printf("Echo task started.\n");

    while (1) {
        // Wait for a frame (100ms block to save CPU)
        if (crater_can_receive(&rx_frame, 10) == CAN_OK) {

            printf("Echoing ID: 0x%x\n", rx_frame.identifier);
            if (crater_can_transmit(&rx_frame, 100) != CAN_OK) {
                printf("Echo transmit failed.\n");
            }

        }
        
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}


// HEARTBEAT TASK
// This task sends a specific frame every 1 second
void can_heartbeat_task(void *pvParameters) {
    can_frame_t heartbeat_frame = {
        .identifier = 0x123,
        .data_length_code = 4,
        .data = {0xDE, 0xAD, 0xBE, 0xEF},
        .is_rtr = false
    };

    printf("Heartbeat task started.\n");

    while (1) {
        if (crater_can_transmit(&heartbeat_frame, 100) == CAN_OK) {
            printf("Heartbeat sent.\n");
        } else {
            printf("Heartbeat failed.\n");
        }

        // Delay for 1000ms
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void) {
    printf("Initializing CAN Node...\n");
    
    if (crater_can_init(TX_PIN, RX_PIN) != CAN_OK) {
        printf("Failed to initialize CAN hardware.\n");
        return;
    }

    // Create the Echo Task (higher priority to respond quickly)
    xTaskCreate(can_echo_task, "can_echo", 3072, NULL, 5, NULL);

    // Create the Heartbeat Task
    xTaskCreate(can_heartbeat_task, "can_heartbeat", 3072, NULL, 4, NULL);
}