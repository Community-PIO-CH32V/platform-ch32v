/********************************** (C) COPYRIGHT *******************************
 * File Name          : APP_USB.h
 * Author             : WCH
 * Version            : V1.1
 * Date               : 2022/01/19
 * Description        :
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * SPDX-License-Identifier: Apache-2.0
 *******************************************************************************/

#ifndef _APP_USB_H
#define _APP_USBE_H

#ifdef __cplusplus
extern "C" {
#endif



extern void app_usb_init(void);

extern void USBSendData( uint8_t *SendBuf, uint8_t l);
/*********************************************************************
*********************************************************************/

#ifdef __cplusplus
}
#endif

#endif /* _BLE_usb_SERVICE_H */
