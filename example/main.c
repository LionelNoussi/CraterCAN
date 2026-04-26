#include <stdio.h>
#include "can_manager.h"

// Note: To run this continuously on ESP32 without crashing the watchdog timer, 
// you must include "freertos/FreeRTOS.h" and "freertos/task.h", then call 
// vTaskDelay() inside your loop. This has been omitted to keep the logic generic.

#define TX_PIN 4
#define RX_PIN 5

void run_echo_test() {
    can_frame_t rx_frame;
    
    // Attempt to receive a message with a 10ms timeout
    if (can_manager_receive(&rx_frame, 10) == CAN_OK) {
        printf("Received message with ID: 0x%X\n", rx_frame.identifier);
        
        // Transmit it back with a 100ms timeout
        if (can_manager_transmit(&rx_frame, 100) == CAN_OK) {
            printf("Successfully echoed message back.\n");
        } else {
            printf("Failed to echo message.\n");
        }
    }
}

int main() {
    printf("Starting CAN Node...\n");
    
    if (can_manager_init(TX_PIN, RX_PIN) != CAN_OK) {
        printf("Failed to initialize CAN hardware.\n");
        return 1;
    }

    while (1) {
        run_echo_test();
        
        // Framework specific delay goes here (e.g., delay(10) or vTaskDelay)
    }

    return 0;
}