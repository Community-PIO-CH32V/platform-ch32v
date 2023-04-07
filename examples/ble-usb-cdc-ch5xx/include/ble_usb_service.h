/********************************** (C) COPYRIGHT *******************************
 * File Name          : BLE_USB_SERVICE.h
 * Author             : WCH
 * Version            : V1.1
 * Date               : 2022/01/19
 * Description        :
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * SPDX-License-Identifier: Apache-2.0
 *******************************************************************************/

#ifndef _BLE_USB_SERVICE_H
#define _BLE_USB_SERVICE_H

#ifdef __cplusplus
extern "C" {
#endif

//#include "att.h"
#include "stdint.h"

#define BLE_USB_RX_BUFF_SIZE    1

typedef enum
{
    BLE_USB_EVT_TX_NOTI_DISABLED = 1,
    BLE_USB_EVT_TX_NOTI_ENABLED,
    BLE_USB_EVT_BLE_DATA_RECIEVED,
} ble_usb_evt_type_t;

typedef struct
{
    uint8_t const *p_data; /**< A pointer to the buffer with received data. */
    uint16_t       length; /**< Length of received data. */
} ble_usb_evt_rx_data_t;

typedef struct
{
    ble_usb_evt_type_t    type;
    ble_usb_evt_rx_data_t data;
} ble_usb_evt_t;

typedef void (*ble_usb_ProfileChangeCB_t)(uint16_t connection_handle, ble_usb_evt_t *p_evt);

/*********************************************************************
 * API FUNCTIONS
 */

/*
 * ble_usb_AddService- Initializes the raw pass GATT Profile service by registering
 *          GATT attributes with the GATT server.
 *
 * @param   services - services to add. This is a bit map and can
 *                     contain more than one service.
 */

extern bStatus_t ble_usb_add_service(ble_usb_ProfileChangeCB_t cb);

extern uint8 ble_usb_notify_is_ready(uint16 connHandle);

extern bStatus_t ble_usb_notify(uint16 connHandle, attHandleValueNoti_t *pNoti, uint8 taskId);
/*********************************************************************
*********************************************************************/

#ifdef __cplusplus
}
#endif

#endif /* _BLE_usb_SERVICE_H */
