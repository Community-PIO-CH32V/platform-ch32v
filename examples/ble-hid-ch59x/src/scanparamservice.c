/********************************** (C) COPYRIGHT *******************************
 * File Name          : scanparamservice.c
 * Author             : WCH
 * Version            : V1.0
 * Date               : 2018/12/10
 * Description        : 扫描参数服务
 *********************************************************************************
 * Copyright (c) 2021 Nanjing Qinheng Microelectronics Co., Ltd.
 * Attention: This software (modified or not) and binary are used for 
 * microcontroller manufactured by Nanjing Qinheng Microelectronics.
 *******************************************************************************/

/*********************************************************************
 * INCLUDES
 */
#include "CONFIG.h"
#include "scanparamservice.h"

/*********************************************************************
 * MACROS
 */

/*********************************************************************
 * CONSTANTS
 */

/*********************************************************************
 * TYPEDEFS
 */

/*********************************************************************
 * GLOBAL VARIABLES
 */
// Scan parameters service
const uint8_t scanParamServUUID[ATT_BT_UUID_SIZE] = {
    LO_UINT16(SCAN_PARAM_SERV_UUID), HI_UINT16(SCAN_PARAM_SERV_UUID)};

// Scan interval window characteristic
const uint8_t scanIntervalWindowUUID[ATT_BT_UUID_SIZE] = {
    LO_UINT16(SCAN_INTERVAL_WINDOW_UUID), HI_UINT16(SCAN_INTERVAL_WINDOW_UUID)};

// Scan parameter refresh characteristic
const uint8_t scanParamRefreshUUID[ATT_BT_UUID_SIZE] = {
    LO_UINT16(SCAN_REFRESH_UUID), HI_UINT16(SCAN_REFRESH_UUID)};

/*********************************************************************
 * EXTERNAL VARIABLES
 */

/*********************************************************************
 * EXTERNAL FUNCTIONS
 */

/*********************************************************************
 * LOCAL VARIABLES
 */

// Application callback
static scanParamServiceCB_t scanParamServiceCB;

/*********************************************************************
 * Profile Attributes - variables
 */

// Scan Parameters Service attribute
static const gattAttrType_t scanParamService = {ATT_BT_UUID_SIZE, scanParamServUUID};

// Scan Interval Window characteristic
static uint8_t scanIntervalWindowProps = GATT_PROP_WRITE_NO_RSP;
static uint8_t scanIntervalWindow[SCAN_INTERVAL_WINDOW_CHAR_LEN];

// Scan Parameter Refresh characteristic
static uint8_t       scanParamRefreshProps = GATT_PROP_NOTIFY;
static uint8_t       scanParamRefresh[SCAN_PARAM_REFRESH_LEN];
static gattCharCfg_t scanParamRefreshClientCharCfg[GATT_MAX_NUM_CONN];

/*********************************************************************
 * Profile Attributes - Table
 */

static gattAttribute_t scanParamAttrTbl[] = {
    // Scan Parameters Service attribute
    {
        {ATT_BT_UUID_SIZE, primaryServiceUUID}, /* type */
        GATT_PERMIT_READ,                       /* permissions */
        0,                                      /* handle */
        (uint8_t *)&scanParamService            /* pValue */
    },

    // Scan Interval Window declaration
    {
        {ATT_BT_UUID_SIZE, characterUUID},
        GATT_PERMIT_READ,
        0,
        &scanIntervalWindowProps},

    // Scan Interval Window characteristic
    {
        {ATT_BT_UUID_SIZE, scanIntervalWindowUUID},
        GATT_PERMIT_ENCRYPT_WRITE,
        0,
        scanIntervalWindow},

    // Scan Parameter Refresh declaration
    {
        {ATT_BT_UUID_SIZE, characterUUID},
        GATT_PERMIT_READ,
        0,
        &scanParamRefreshProps},

    // Scan Parameter Refresh characteristic
    {
        {ATT_BT_UUID_SIZE, scanParamRefreshUUID},
        0,
        0,
        scanParamRefresh},

    // Scan Parameter Refresh characteristic client characteristic configuration
    {
        {ATT_BT_UUID_SIZE, clientCharCfgUUID},
        GATT_PERMIT_READ | GATT_PERMIT_ENCRYPT_WRITE,
        0,
        (uint8_t *)&scanParamRefreshClientCharCfg}
};

// Attribute index enumeration-- these indexes match array elements above
enum
{
    SCAN_PARAM_SERVICE_IDX,       // Scan Parameters Service
    SCAN_PARAM_INTERVAL_DECL_IDX, // Scan Interval Window declaration
    SCAN_PARAM_INTERVAL_IDX,      // Scan Interval Window characteristic
    SCAN_PARAM_REFRESH_DECL_IDX,  // Scan Parameter Refresh declaration
    SCAN_PARAM_REFRESH_IDX,       // Scan Parameter Refresh characteristic
    SCAN_PARAM_REFRESH_CCCD_IDX   // Scan Parameter Refresh characteristic client characteristic configuration
};

/*********************************************************************
 * LOCAL FUNCTIONS
 */
static bStatus_t scanParamWriteAttrCB(uint16_t connHandle, gattAttribute_t *pAttr,
                                      uint8_t *pValue, uint16_t len, uint16_t offset, uint8_t method);
static bStatus_t scanParamReadAttrCB(uint16_t connHandle, gattAttribute_t *pAttr,
                                     uint8_t *pValue, uint16_t *pLen, uint16_t offset, uint16_t maxLen, uint8_t method);

/*********************************************************************
 * PROFILE CALLBACKS
 */

// Service Callbacks
gattServiceCBs_t scanParamCBs = {
    scanParamReadAttrCB,  // Read callback function pointer
    scanParamWriteAttrCB, // Write callback function pointer
    NULL                  // Authorization callback function pointer
};

/*********************************************************************
 * PUBLIC FUNCTIONS
 */

/*********************************************************************
 * @fn      ScanParam_AddService
 *
 * @brief   Initializes the Battery Service by registering
 *          GATT attributes with the GATT server.
 *
 * @return  Success or Failure
 */
bStatus_t ScanParam_AddService(void)
{
    uint8_t status = SUCCESS;

    // Initialize Client Characteristic Configuration attributes
    GATTServApp_InitCharCfg(INVALID_CONNHANDLE, scanParamRefreshClientCharCfg);

    // Register GATT attribute list and CBs with GATT Server App
    status = GATTServApp_RegisterService(scanParamAttrTbl, GATT_NUM_ATTRS(scanParamAttrTbl), GATT_MAX_ENCRYPT_KEY_SIZE,
                                         &scanParamCBs);

    return (status);
}

/*********************************************************************
 * @fn      ScanParam_Register
 *
 * @brief   Register a callback function with the Battery Service.
 *
 * @param   pfnServiceCB - Callback function.
 *
 * @return  None.
 */
extern void ScanParam_Register(scanParamServiceCB_t pfnServiceCB)
{
    scanParamServiceCB = pfnServiceCB;
}

/*********************************************************************
 * @fn      ScanParam_SetParameter
 *
 * @brief   Set a Battery Service parameter.
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
bStatus_t ScanParam_SetParameter(uint8_t param, uint8_t len, void *value)
{
    bStatus_t ret = SUCCESS;

    switch(param)
    {
        default:
            ret = INVALIDPARAMETER;
            break;
    }

    return (ret);
}

/*********************************************************************
 * @fn      ScanParam_GetParameter
 *
 * @brief   Get a Battery Service parameter.
 *
 * @param   param - Profile parameter ID
 * @param   value - pointer to data to get.  This is dependent on
 *          the parameter ID and WILL be cast to the appropriate
 *          data type (example: data type of uint16_t will be cast to
 *          uint16_t pointer).
 *
 * @return  bStatus_t
 */
bStatus_t ScanParam_GetParameter(uint8_t param, void *value)
{
    bStatus_t ret = SUCCESS;
    switch(param)
    {
        case SCAN_PARAM_PARAM_INTERVAL:
            *((uint16_t *)value) = BUILD_UINT16(scanIntervalWindow[0],
                                                scanIntervalWindow[1]);
            break;

        case SCAN_PARAM_PARAM_WINDOW:
            *((uint16_t *)value) = BUILD_UINT16(scanIntervalWindow[2],
                                                scanIntervalWindow[3]);
            break;

        default:
            ret = INVALIDPARAMETER;
            break;
    }

    return (ret);
}

/*********************************************************************
 * @fn      ScanParam_RefreshNotify
 *
 * @brief   Notify the peer to refresh the scan parameters.
 *
 * @param   connHandle - connection handle
 *
 * @return  None
 */
void ScanParam_RefreshNotify(uint16_t connHandle)
{
    uint16_t value;

    value = GATTServApp_ReadCharCfg(connHandle, scanParamRefreshClientCharCfg);
    if(value & GATT_CLIENT_CFG_NOTIFY)
    {
        attHandleValueNoti_t noti;

        noti.pValue = GATT_bm_alloc(connHandle, ATT_HANDLE_VALUE_NOTI,
                                    SCAN_PARAM_REFRESH_LEN, NULL, 0);
        if(noti.pValue != NULL)
        {
            // send notification
            noti.handle = scanParamAttrTbl[SCAN_PARAM_REFRESH_CCCD_IDX].handle;
            noti.len = SCAN_PARAM_REFRESH_LEN;
            noti.pValue[0] = SCAN_PARAM_REFRESH_REQ;

            if(GATT_Notification(connHandle, &noti, FALSE) != SUCCESS)
            {
                GATT_bm_free((gattMsg_t *)&noti, ATT_HANDLE_VALUE_NOTI);
            }
        }
    }
}

/*********************************************************************
 * @fn          scanParamReadAttrCB
 *
 * @brief       GATT read callback.
 *
 * @param       connHandle - connection message was received on
 * @param       pAttr - pointer to attribute
 * @param       pValue - pointer to data to be read
 * @param       pLen - length of data to be read
 * @param       offset - offset of the first octet to be read
 * @param       maxLen - maximum length of data to be read
 *
 * @return      Success or Failure
 */
static bStatus_t scanParamReadAttrCB(uint16_t connHandle, gattAttribute_t *pAttr,
                                     uint8_t *pValue, uint16_t *pLen, uint16_t offset, uint16_t maxLen, uint8_t method)
{
    bStatus_t status = SUCCESS;

    return (status);
}

/*********************************************************************
 * @fn      scanParamWriteAttrCB
 *
 * @brief   Validate attribute data prior to a write operation
 *
 * @param   connHandle - connection message was received on
 * @param   pAttr - pointer to attribute
 * @param   pValue - pointer to data to be written
 * @param   len - length of data
 * @param   offset - offset of the first octet to be written
 *
 * @return  Success or Failure
 */
static bStatus_t scanParamWriteAttrCB(uint16_t connHandle, gattAttribute_t *pAttr,
                                      uint8_t *pValue, uint16_t len, uint16_t offset, uint8_t method)
{
    uint16_t  uuid;
    bStatus_t status = SUCCESS;

    // Make sure it's not a blob operation (no attributes in the profile are long)
    if(offset > 0)
    {
        return (ATT_ERR_ATTR_NOT_LONG);
    }

    uuid = BUILD_UINT16(pAttr->type.uuid[0], pAttr->type.uuid[1]);

    // Only one writeable attribute
    if(uuid == SCAN_INTERVAL_WINDOW_UUID)
    {
        if(len == SCAN_INTERVAL_WINDOW_CHAR_LEN)
        {
            uint16_t interval = BUILD_UINT16(pValue[0], pValue[1]);
            uint16_t window = BUILD_UINT16(pValue[0], pValue[1]);

            // Validate values
            if(window <= interval)
            {
                tmos_memcpy(pAttr->pValue, pValue, len);

                (*scanParamServiceCB)(SCAN_INTERVAL_WINDOW_SET);
            }
            else
            {
                status = ATT_ERR_INVALID_VALUE;
            }
        }
        else
        {
            status = ATT_ERR_INVALID_VALUE_SIZE;
        }
    }
    else if(uuid == GATT_CLIENT_CHAR_CFG_UUID)
    {
        status = GATTServApp_ProcessCCCWriteReq(connHandle, pAttr, pValue, len,
                                                offset, GATT_CLIENT_CFG_NOTIFY);
    }
    else
    {
        status = ATT_ERR_ATTR_NOT_FOUND;
    }

    return (status);
}

/*********************************************************************
 * @fn          ScanParam_HandleConnStatusCB
 *
 * @brief       Service link status change handler function.
 *
 * @param       connHandle - connection handle
 * @param       changeType - type of change
 *
 * @return      none
 */
void ScanParam_HandleConnStatusCB(uint16_t connHandle, uint8_t changeType)
{
    // Make sure this is not loopback connection
    if(connHandle != LOOPBACK_CONNHANDLE)
    {
        // Reset Client Char Config if connection has dropped
        if((changeType == LINKDB_STATUS_UPDATE_REMOVED) ||
           ((changeType == LINKDB_STATUS_UPDATE_STATEFLAGS) &&
            (!linkDB_Up(connHandle))))
        {
            GATTServApp_InitCharCfg(connHandle, scanParamRefreshClientCharCfg);
        }
    }
}
