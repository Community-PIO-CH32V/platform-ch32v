/********************************** (C) COPYRIGHT *******************************
 * File Name          : scanparamservice.h
 * Author             : WCH
 * Version            : V1.0
 * Date               : 2018/12/11
 * Description        :
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

#ifndef SCANPARAMSERVICE_H
#define SCANPARAMSERVICE_H

#ifdef __cplusplus
extern "C" {
#endif

/*********************************************************************
 * INCLUDES
 */

/*********************************************************************
 * CONSTANTS
 */

// Scan Characteristic Lengths
#define SCAN_INTERVAL_WINDOW_CHAR_LEN    4
#define SCAN_PARAM_REFRESH_LEN           1

// Scan Parameter Refresh Values
#define SCAN_PARAM_REFRESH_REQ           0x00

// Callback events
#define SCAN_INTERVAL_WINDOW_SET         1

// Get/Set parameters
#define SCAN_PARAM_PARAM_INTERVAL        0
#define SCAN_PARAM_PARAM_WINDOW          1

/*********************************************************************
 * TYPEDEFS
 */

/*********************************************************************
 * MACROS
 */

/*********************************************************************
 * Profile Callbacks
 */

// Scan Parameters Service callback function
typedef void (*scanParamServiceCB_t)(uint8_t event);

/*********************************************************************
 * API FUNCTIONS
 */

/*********************************************************************
 * @fn      ScanParam_AddService
 *
 * @brief   Initializes the Service by registering
 *          GATT attributes with the GATT server.
 *
 * @return  Success or Failure
 */
extern bStatus_t ScanParam_AddService(void);

/*********************************************************************
 * @fn      ScanParam_Register
 *
 * @brief   Register a callback function with the Scan Parameters Service.
 *
 * @param   pfnServiceCB - Callback function.
 *
 * @return  None.
 */
extern void ScanParam_Register(scanParamServiceCB_t pfnServiceCB);

/*********************************************************************
 * @fn      ScanParam_SetParameter
 *
 * @brief   Set a Scan Parameters Service parameter.
 *
 * @param   param - Profile parameter ID
 * @param   len - length of data to right
 * @param   value - pointer to data to write.  This is dependent on
 *          the parameter ID and WILL be cast to the appropriate
 *          data type (example: data type of uint16_t will be cast to
 *          uint16_t pointer).
 *
 * @return  bStatus_t
 */
extern bStatus_t ScanParam_SetParameter(uint8_t param, uint8_t len, void *value);

/*********************************************************************
 * @fn      ScanParam_GetParameter
 *
 * @brief   Get a Scan Parameters Service parameter.
 *
 * @param   param - Profile parameter ID
 * @param   value - pointer to data to get.  This is dependent on
 *          the parameter ID and WILL be cast to the appropriate
 *          data type (example: data type of uint16_t will be cast to
 *          uint16_t pointer).
 *
 * @return  bStatus_t
 */
extern bStatus_t ScanParam_GetParameter(uint8_t param, void *value);

/*********************************************************************
 * @fn      ScanParam_RefreshNotify
 *
 * @brief   Notify the peer to refresh the scan parameters.
 *
 * @param   connHandle - connection handle
 *
 * @return  None
 */
extern void ScanParam_RefreshNotify(uint16_t connHandle);

extern void ScanParam_HandleConnStatusCB(uint16_t connHandle, uint8_t changeType);

/*********************************************************************
*********************************************************************/

#ifdef __cplusplus
}
#endif

#endif /* SCANPARAMSERVICE_H */
