#include "crater_can.h"
#include "driver/twai.h"
#include <string.h>

// Fallback if not compiled inside FreeRTOS environment
#ifndef portTICK_PERIOD_MS
#define portTICK_PERIOD_MS 1 
#endif

can_err_t crater_can_init(int tx_pin, int rx_pin) {
    twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT((gpio_num_t)tx_pin, (gpio_num_t)rx_pin, TWAI_MODE_NORMAL);
    twai_timing_config_t t_config = TWAI_TIMING_CONFIG_500KBITS();
    twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

    if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
        return CAN_ERR_FAIL;
    }

    if (twai_start() != ESP_OK) {
        return CAN_ERR_FAIL;
    }

    return CAN_OK;
}

can_err_t crater_can_transmit(const can_frame_t* frame, uint32_t timeout_ms) {
    if (frame == NULL) return CAN_ERR_INVALID_ARG;
    if (frame->data_length_code > 8) return CAN_ERR_INVALID_ARG;

    twai_message_t twai_msg = {0};
    twai_msg.identifier = frame->identifier;
    twai_msg.extd = 0; // 0 for standard frame, 1 for extended
    twai_msg.rtr = frame->is_rtr ? 1 : 0;
    twai_msg.data_length_code = frame->data_length_code;

    if (!frame->is_rtr && frame->data_length_code > 0) {
        memcpy(twai_msg.data, frame->data, frame->data_length_code);
    }

    esp_err_t err = twai_transmit(&twai_msg, timeout_ms / portTICK_PERIOD_MS);
    if (err == ESP_ERR_TIMEOUT) return CAN_ERR_TIMEOUT;
    if (err != ESP_OK) return CAN_ERR_FAIL;

    return CAN_OK;
}

can_err_t crater_can_receive(can_frame_t* frame, uint32_t timeout_ms) {
    if (frame == NULL) return CAN_ERR_INVALID_ARG;

    twai_message_t twai_msg;
    esp_err_t err = twai_receive(&twai_msg, timeout_ms / portTICK_PERIOD_MS);
    
    if (err == ESP_ERR_TIMEOUT) return CAN_ERR_TIMEOUT;
    if (err != ESP_OK) return CAN_ERR_FAIL;

    frame->identifier = twai_msg.identifier;
    frame->data_length_code = twai_msg.data_length_code;
    frame->is_rtr = (twai_msg.rtr == 1);
    
    if (frame->data_length_code > 0) {
        memcpy(frame->data, twai_msg.data, frame->data_length_code);
    }

    return CAN_OK;
}