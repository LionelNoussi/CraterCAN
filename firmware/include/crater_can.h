#ifndef CRATER_CAN_H
#define CRATER_CAN_H

#include <stdint.h>
#include <stdbool.h>

// Custom error definitions to decouple from ESP-IDF's esp_err_t
typedef enum {
    CAN_OK = 0,
    CAN_ERR_FAIL = 1,
    CAN_ERR_TIMEOUT = 2,
    CAN_ERR_INVALID_ARG = 3
} can_err_t;

// Platform-agnostic CAN frame structure
typedef struct {
    uint32_t identifier;
    uint8_t data_length_code;
    uint8_t data[8];
    bool is_rtr;
} can_frame_t;

/*
 * Initializes the CAN hardware.
 * tx_pin: Transmit GPIO pin
 * rx_pin: Receive GPIO pin
 */
can_err_t crater_can_init(int tx_pin, int rx_pin);

/*
 * Transmits a CAN frame.
 * frame: Pointer to the frame data
 * timeout_ms: Maximum time to wait in queue
 */
can_err_t crater_can_transmit(const can_frame_t* frame, uint32_t timeout_ms);

/*
 * Receives a CAN frame.
 * frame: Pointer to populate with incoming data
 * timeout_ms: Maximum time to wait for a message
 */
can_err_t crater_can_receive(can_frame_t* frame, uint32_t timeout_ms);

#endif // CRATER_CAN_H